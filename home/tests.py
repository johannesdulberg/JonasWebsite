from home.models import HomePage

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase


class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests for basic page structure setup and HomePage creation.
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page)

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Tests for homepage functionality and rendering.
    """

    def setUp(self):
        """
        Create a homepage instance for testing.
        """
        root_page = Page.get_first_root_node()
        Site.objects.create(
            hostname="testsite", root_page=root_page, is_default_site=True
        )
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)

    def test_homepage_is_renderable(self):
        self.assertPageIsRenderable(self.homepage)

    def test_homepage_template_used(self):
        response = self.client.get(self.homepage.url)
        self.assertTemplateUsed(response, "home/home_page.html")


class ImportWixTests(WagtailPageTestCase):
    """Der Import legt Bilder an und füllt die Galerien wie ein Redakteur im Admin."""

    def make_source(self, folder, skip=()):
        from PIL import Image as PillowImage

        from home.management.commands.import_wix import HOME_BOTTOM, HOME_TOP

        home = folder / "home"
        home.mkdir()
        for number, (wix_id, _focal) in enumerate(HOME_TOP + HOME_BOTTOM, start=1):
            if wix_id in skip:
                continue
            # Jede Datei bekommt eine andere Farbe, sonst hätten alle dieselbe Prüfsumme.
            PillowImage.new("RGB", (60, 40), (number * 5, 80, 120)).save(
                home / f"{number:03d}_c5ec14_{wix_id}.jpg"
            )

    def run_import(self, source, *args):
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("import_wix", "--quelle", str(source), *args, stdout=out)
        return out.getvalue()

    def test_fills_both_galleries_in_order_with_focal_points(self):
        import tempfile
        from pathlib import Path

        from django.test import override_settings

        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp + "/media"):
            source = Path(tmp) / "wix_import"
            source.mkdir()
            self.make_source(source)
            self.run_import(source)

            home = HomePage.objects.get(pk=Site.objects.get(is_default_site=True).root_page_id)
            top = list(home.top_gallery_images.all())
            self.assertEqual(len(top), 25)
            self.assertEqual(home.bottom_gallery_images.count(), 19)
            self.assertEqual(top[0].image.title, "Startseite Oben 01")
            self.assertIsNone(top[0].image.focal_point_x)
            # Zweites Bild: Fokuspunkt (0.5, 0.32) auf einem Bild mit 60 x 40 Pixeln.
            self.assertEqual((top[1].image.focal_point_x, top[1].image.focal_point_y), (30, 13))
            self.assertEqual(top[0].image.collection.name, "Startseite")

            response = self.client.get("/")
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertEqual(html.count("<img"), 44)
            self.assertIn("fill-320x912", html)

            # Zweiter Lauf ändert nichts, --neu befüllt ohne Bilder doppelt anzulegen.
            self.assertIn("unverändert", self.run_import(source))
            self.run_import(source, "--neu")
            home.refresh_from_db()
            self.assertEqual(home.top_gallery_images.count(), 25)
            from wagtail.images import get_image_model

            self.assertEqual(get_image_model().objects.count(), 44)

    def test_missing_files_are_reported_and_skipped(self):
        import tempfile
        from pathlib import Path

        from django.test import override_settings

        from home.management.commands.import_wix import HOME_TOP

        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp + "/media"):
            source = Path(tmp) / "wix_import"
            source.mkdir()
            self.make_source(source, skip={HOME_TOP[3][0]})
            output = self.run_import(source)
            self.assertIn("1 Fotos fehlen", output)
            home = HomePage.objects.get(pk=Site.objects.get(is_default_site=True).root_page_id)
            self.assertEqual(home.top_gallery_images.count(), 24)
