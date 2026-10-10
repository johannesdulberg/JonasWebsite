import json
import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image as PillowImage
from wagtail.images import get_image_model
from wagtail.models import Page, Site

from core.models import SiteSettings
from home.models import HomePage
from pages.management.commands.import_wix import HOME_BOTTOM, HOME_TOP
from pages.models import AboutPage, BookingPage, GalleryPage, StandardPage

ACCOUNT = "c5ec14"


def fake_id(number):
    return f"{number:032x}"


class WixSource:
    """Baut einen wix_import-Ordner nach, wie ihn scripts/fetch_wix_images.py anlegt."""

    def __init__(self, folder):
        self.folder = folder
        self.pages = {}
        self.counter = 1000

    def image_file(self, page, wid, size=(60, 40)):
        folder = self.folder / page
        folder.mkdir(exist_ok=True)
        number = len(list(folder.glob("*.jpg"))) + 1
        self.counter += 1
        # Jede Datei bekommt eine andere Farbe, sonst hätten alle dieselbe Prüfsumme.
        color = (self.counter % 250, (self.counter * 7) % 250, 120)
        PillowImage.new("RGB", size, color).save(folder / f"{number:03d}_{ACCOUNT}_{wid}.jpg")

    def image(self, page, tile=None, focal_point=None, size=(60, 40)):
        self.counter += 1
        wid = fake_id(self.counter)
        self.image_file(page, wid, size)
        entry = {"type": "image", "id": f"{ACCOUNT}_{wid}~mv2.jpg", "alt": ""}
        if tile:
            entry["width"], entry["height"] = tile
        if focal_point:
            entry["focal_point"] = list(focal_point)
        return entry

    @staticmethod
    def text(tag, text, html=None):
        return {"type": "text", "tag": tag, "text": text, "html": html or text}

    def write(self):
        (self.folder / "manifest.json").write_text(
            json.dumps({"pages": {name: {"items": [], "content": content} for name, content in self.pages.items()}})
        )


class ImportTestCase(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        media = override_settings(MEDIA_ROOT=self.tmp.name + "/media")
        media.enable()
        self.addCleanup(media.disable)

        folder = Path(self.tmp.name) / "wix_import"
        folder.mkdir()
        self.source = source = WixSource(folder)
        t = source.text

        for wid, _focal in HOME_TOP + HOME_BOTTOM:
            source.image_file("home", wid)

        source.pages["commercial"] = [source.image("commercial", tile=(452, 322)) for _ in range(3)] + [
            t("p", 'Handy Wallpaper "Waves"'),
            t("p", "© 2025 Jonas Dülberg"),
        ]
        source.pages["outdoor"] = [source.image("outdoor", tile=(522, 348)) for _ in range(2)]
        source.pages["other"] = (
            [t("h2", "Cinemagramm"), t("p", "Kurze Bild-Video-Hybride.")]
            + [t("h2", "Portaits")]
            + [source.image("other", tile=(121, 345), focal_point=(0.5, 0.25)) for _ in range(3)]
            + [t("h2", "Reitsport")]
            + [source.image("other", tile=(160, 456)) for _ in range(2)]
            + [t("h2", "Leer")]
        )
        (folder / "other" / "video_01_abc.mp4").write_bytes(b"kein echtes Video")
        source.pages["booking"] = [
            t("p", "Verschiedene Projekte erfordern verschiedene Herangehensweisen."),
            t("p", "Ich freu mich von Ihnen zu hören!"),
            source.image("booking", tile=(121, 345), focal_point=(0.51, 0.3)),
            source.image("booking", tile=(121, 345)),
            t("h2", "Kontakt"),
            t("p", "jemand@example.com"),
            t("p", "+4915700000000"),
            {"type": "field", "kind": "input", "input_type": "text", "name": "name", "label": "Name", "required": True},
            t("p", "Danke! Die Nachricht wurde gesendet."),
            t("button", "Send"),
        ]
        source.pages["about"] = [
            t("p", "Fotografie war zunächst ein Hobby."),
            t("p", "Mehr auf Instagram.", 'Mehr auf <a href="https://instagram.com/example">Instagram</a>.'),
            source.image("about", tile=(309, 308), size=(50, 50)),
        ]
        source.pages["impressum"] = [
            t("h2", "Impressum"),
            t("p", "Angaben gemäß Gesetz", "Angaben gemäß Gesetz<br>Zweite Zeile"),
            t("h2", "Datenschutzerklärung"),
            t("h4", "Cookies"),
            t("li", "Erster Punkt"),
            t("li", "Zweiter Punkt"),
            t("p", "Schluss."),
        ]
        source.write()
        self.site = Site.objects.get(is_default_site=True)

    def run_import(self, *args):
        out = StringIO()
        call_command("import_wix", "--quelle", str(self.source.folder), *args, stdout=out)
        return out.getvalue()


class ImportWixTests(ImportTestCase):
    def test_home_galleries_keep_order_and_focal_points(self):
        self.run_import("--seite", "home")
        home = HomePage.objects.get(pk=self.site.root_page_id)
        top = list(home.top_gallery_images.all())
        self.assertEqual(len(top), 25)
        self.assertEqual(home.bottom_gallery_images.count(), 19)
        self.assertEqual(top[0].image.title, "Startseite Oben 01")
        self.assertIsNone(top[0].image.focal_point_x)
        # Zweites Bild: Fokuspunkt (0.5, 0.32) auf einem Bild mit 60 x 40 Pixeln.
        self.assertEqual((top[1].image.focal_point_x, top[1].image.focal_point_y), (30, 13))

        html = self.client.get("/").content.decode()
        self.assertEqual(html.count("data-lightbox-item"), 44)
        self.assertEqual(html.count("data-lightbox-group"), 2)
        self.assertIn("fill-320x912", html)
        self.assertIn("max-2000x2000", html)

    def test_all_pages_are_filled_and_render(self):
        output = self.run_import()
        home = self.site.root_page

        commercial = GalleryPage.objects.get(slug="commercial")
        section = commercial.sections.get()
        self.assertEqual((section.layout, section.images.count(), section.text), ("grid", 3, ""))

        other = GalleryPage.objects.get(slug="other")
        sections = list(other.sections.all())
        self.assertEqual([s.heading for s in sections], ["Cinemagramm", "Portaits", "Reitsport"])
        self.assertEqual([s.layout for s in sections], ["grid", "strip_small", "strip_large"])
        self.assertEqual([s.images.count() for s in sections], [0, 3, 2])
        self.assertEqual(sections[0].videos.count(), 1)
        self.assertEqual(sections[0].text, "<p>Kurze Bild-Video-Hybride.</p>")
        self.assertIn("Abschnitt ohne Bilder ausgelassen: Leer", output)

        booking = BookingPage.objects.get(slug="booking")
        self.assertEqual(booking.strip_images.count(), 2)
        self.assertIn("Ich freu mich", booking.intro)
        for unwanted in ["example.com", "+4915700000000", "Kontakt", "gesendet", "Send"]:
            self.assertNotIn(unwanted, booking.intro)
        self.assertIn("Formularfelder bei Wix: Name", output)

        about = AboutPage.objects.get(slug="about")
        self.assertIn('<a href="https://instagram.com/example">Instagram</a>', about.body)
        self.assertIsNotNone(about.image)

        impressum = StandardPage.objects.get(slug="impressum")
        self.assertEqual(
            impressum.body,
            "<p>Angaben gemäß Gesetz<br/>Zweite Zeile</p><h2>Datenschutzerklärung</h2><h3>Cookies</h3>"
            "<ul><li>Erster Punkt</li><li>Zweiter Punkt</li></ul><p>Schluss.</p>",
        )

        self.assertEqual(
            [page.slug for page in home.get_children().live().in_menu()],
            ["commercial", "outdoor", "other", "booking", "about"],
        )
        for slug, expected in [
            ("commercial", "data-lightbox-item"),
            ("outdoor", "data-lightbox-item"),
            ("other", "<video"),
            ("booking", "data-inactive-form"),
            ("about", "Fotografie war"),
            ("impressum", "Datenschutzerklärung"),
        ]:
            response = self.client.get(f"/{slug}/")
            self.assertEqual(response.status_code, 200, slug)
            self.assertIn(expected, response.content.decode(), slug)

        # Fußzeilen-Texte von Wix landen nicht im Inhalt.
        self.assertNotIn("Wallpaper", self.client.get("/commercial/").content.decode().split("<footer")[0])

    def test_second_run_changes_nothing_and_neu_does_not_duplicate(self):
        self.run_import()
        Image = get_image_model()
        images, pages = Image.objects.count(), Page.objects.count()

        output = self.run_import()
        self.assertEqual(output.count("unverändert"), 8)  # zwei Galerien der Startseite + sechs Seiten
        self.run_import("--neu")
        self.assertEqual((Image.objects.count(), Page.objects.count()), (images, pages))
        self.assertEqual(GalleryPage.objects.get(slug="other").sections.count(), 3)

    def test_placeholders_are_replaced_in_place(self):
        home = self.site.root_page
        for title in ["Commercial", "Outdoor", "Other", "Booking", "About"]:
            home.add_child(instance=HomePage(title=title, slug=title.lower(), show_in_menus=True))
        placeholder = home.add_child(instance=HomePage(title="Impressum", slug="impressum"))
        extra = home.add_child(instance=HomePage(title="Eigene Seite", slug="eigene", show_in_menus=True))
        settings = SiteSettings.for_site(self.site)
        settings.legal_page = Page.objects.get(pk=placeholder.pk)
        settings.save()

        self.run_import("--seite", "impressum")

        home = Page.objects.get(pk=home.pk)
        self.assertEqual(
            [(page.slug, page.specific_class.__name__) for page in home.get_children()],
            [
                ("eigene", "HomePage"),
                ("commercial", "GalleryPage"),
                ("outdoor", "GalleryPage"),
                ("other", "GalleryPage"),
                ("booking", "BookingPage"),
                ("about", "AboutPage"),
                ("impressum", "StandardPage"),
            ],
        )
        self.assertTrue(Page.objects.filter(pk=extra.pk).exists())
        legal = SiteSettings.for_site(self.site).legal_page
        self.assertEqual(legal.specific_class, StandardPage)
        self.assertIn('href="/impressum/"', self.client.get("/").content.decode())

    def test_without_texts_in_manifest_galleries_still_work(self):
        (self.source.folder / "manifest.json").unlink()
        output = self.run_import("--seite", "commercial", "--seite", "about")
        self.assertEqual(GalleryPage.objects.get(slug="commercial").sections.get().images.count(), 3)
        self.assertIn("Keine Texte im Manifest", output)
        self.assertEqual(AboutPage.objects.get(slug="about").body, "")


class AdminTests(ImportTestCase):
    def test_edit_views_open_for_all_page_types(self):
        self.run_import()
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
        self.client.force_login(user)
        for page in [self.site.root_page, *self.site.root_page.get_children()]:
            response = self.client.get(f"/admin/pages/{page.pk}/edit/")
            self.assertEqual(response.status_code, 200, page.slug)
        html = self.client.get(f"/admin/pages/{GalleryPage.objects.get(slug='other').pk}/edit/").content.decode()
        self.assertIn("Abschnitte", html)
        self.assertIn("Reitsport", html)
