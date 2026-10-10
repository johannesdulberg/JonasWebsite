"""Übernimmt Fotos, Videos und Texte der Wix-Seite in Wagtail.

    docker compose exec web python manage.py import_wix

Voraussetzung: Der Ordner wix_import/ ist gefüllt (scripts/fetch_wix_images.py).

Der Befehl tut dasselbe wie jemand im Admin: Er lädt Fotos in die
Bildbibliothek (eine Sammlung pro Seite), setzt Fokuspunkte, trägt Texte ein
und veröffentlicht die Seiten. Danach lässt sich alles im Admin bearbeiten.

Eine Seite, die schon Inhalt hat, bleibt unverändert. Mit --neu wird ihr
Inhalt ersetzt (Bilder in der Bibliothek bleiben erhalten). Mit --seite lässt
sich das auf einzelne Seiten begrenzen, z. B. --seite other --neu.
"""

import json
import re
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.models import Collection, Site

from home.models import HomeBottomGalleryImage, HomePage, HomeTopGalleryImage
from pages.models import (
    BookingStripImage,
    GallerySection,
    GallerySectionImage,
    GallerySectionVideo,
)
from pages.setup import ensure_pages

# Die beiden Galerien der Wix-Startseite in ihrer Reihenfolge.
# Jeder Eintrag: (Wix-Datei-ID ohne Konto-Präfix, Fokuspunkt).
# Der Fokuspunkt ist die Stelle, die beim Beschneiden auf das Hochformat im Bild
# bleiben soll, als Anteil von links und von oben. Die Werte stammen aus den
# Bildadressen der Wix-Seite (fp_0.5_0.32); None heißt Bildmitte.
HOME_TOP = [
    ("46df2305c87c49f0a4a3d3d98747aeaa", None),
    ("e66338ab7d6b4cbcbd51a3da943f334a", (0.5, 0.32)),
    ("7980ed2ba8ec4d3abb1ccaae01d8e71e", None),
    ("f82ca79aec7b4c319c41326c80c4e954", None),
    ("5f727d63435d4976ae6439b37c2db5ce", None),
    ("163247d59ebe44699721d1289be07c76", (0.5, 0.53)),
    ("842b29fbc3104a9d8cd0d0898951df56", (0.5, 0.43)),
    ("163366d5b19d4311a9864c7e810510ab", (0.42, 0.57)),
    ("219bb54cc00b41719af6d1f2c8a14d0f", (0.47, 0.52)),
    ("f7f9bfe4754244c9ae87f785c7dbcda7", (0.52, 0.36)),
    ("ea14c7c29b98410eb9bb26a134bcb772", (0.49, 0.52)),
    ("bc3f4fda768047bc877c612200a2dedc", (0.66, 0.47)),
    ("de7d485428734d08b0837d07ba5f03b8", (0.44, 0.25)),
    ("34c66ac8310646da90fccd5dbaf3a461", None),
    ("59bc1fd7497d4768aff6f4c1b26b1770", (0.69, 0.48)),
    ("4d7a33a1acdf464ba5f65740e17f0fb8", None),
    ("947c432a9a194e04a30ba2ca900a9811", (0.48, 0.38)),
    ("dee8ae9bfa694c71ab9f164ecaf7696a", (0.47, 0.37)),
    ("1fb86510624742dcbddd87b3a4e2b143", (0.73, 0.37)),
    ("1b57d58e95204f8da3a8c732797c933c", (0.5, 0.44)),
    ("127b04ce29d3487387efb090832313d9", None),
    ("3714b7ed841642d19a6f1f6c69ff719d", (0.53, 0.53)),
    ("fb58c9eb603c4acc88b6ca056d9834d4", (0.5, 0.31)),
    ("47ff010bc6f34490aa590f547c5146c9", (0.46, 0.43)),
    ("0ba96148b5ef4a99b216eda7b2931c0b", None),
]

HOME_BOTTOM = [
    ("0dcc773a14e24421a63a2c9e87dc99d9", (0.34, 0.62)),
    ("465576f9435d43bfa94a71f39e309829", None),
    ("8087046bbc6e40bf8ac1b29c72dcbe47", (0.49, 0.59)),
    ("3c3dc19f0b4c4b348f387f51ae33b26f", None),
    ("a84d63a9cec346e0a2cf8eb164b7df65", (0.49, 0.53)),
    ("67da7a5d1cd3436d96ba68f2e3af0e41", (0.5, 0.66)),
    ("60e5284fac9249ff85ec3c00344405ef", None),
    ("1c3f325b20844ebab97323ea0005e46b", (0.58, 0.62)),
    ("d387515913d34c1bb4198bd223c7a6f6", None),
    ("c5e7048275d64f2aac16da405b7f9678", None),
    ("b2b2f62a7e4a4b2aac8c829bc71682f8", None),
    ("dad239e245c24bd293c6b0a736af0ee3", (0.48, 0.55)),
    ("16879cd7c7fe417aae085fd19ae7fd47", (0.38, 0.46)),
    ("c7daa77dde2b4361a8849bb6bf5f3168", (0.53, 0.58)),
    ("27c8917925044cec907443461ba2e085", None),
    ("2ee8935c439c4b1eaec5424321fee38f", None),
    ("07556fd42efe4b92b17d0de76b4dc7b7", (0.5, 0.6)),
    ("43fc6fabf86c42529766faad37db811a", (0.58, 0.57)),
    ("2614d4fb38d54615baaca35a14e7e193", (0.4, 0.46)),
]

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

# Texte, die auf jeder Wix-Seite stehen und zur Fußzeile gehören.
BOILERPLATE = re.compile(r"^(download$|handy wallpaper|zum download|©|impressum / datenschutz)", re.I)
# Zeilen der Booking-Seite, die im neuen Aufbau aus den Einstellungen kommen.
CONTACT_LINE = re.compile(r"(@|^\+?[\d\s/()-]{7,}$|^kontakt$|nachricht wurde gesendet)", re.I)


def wix_id(value):
    """'c5ec14_<id>~mv2.jpg' oder '007_c5ec14_<id>' -> '<id>'."""
    match = re.search(r"([0-9a-f]{32})", value)
    return match.group(1) if match else ""


class Command(BaseCommand):
    help = "Übernimmt Fotos, Videos und Texte aus wix_import/ in die Seiten."

    def add_arguments(self, parser):
        parser.add_argument(
            "--neu",
            action="store_true",
            help="Inhalt ersetzen, auch wenn eine Seite schon Inhalt hat.",
        )
        parser.add_argument(
            "--seite",
            action="append",
            choices=["home", "commercial", "outdoor", "other", "booking", "about", "impressum"],
            help="Nur diese Seite bearbeiten (mehrfach angebbar). Standard: alle.",
        )
        parser.add_argument(
            "--quelle",
            default=str(Path(settings.BASE_DIR) / "wix_import"),
            help="Ordner mit den heruntergeladenen Dateien (Standard: wix_import im Projekt).",
        )

    # ------------------------------------------------------------------ Ablauf

    def handle(self, *args, **options):
        self.source = Path(options["quelle"])
        if not self.source.is_dir():
            raise CommandError(
                f"{self.source} fehlt. Zuerst laden: python scripts/fetch_wix_images.py"
            )
        self.force = options["neu"]
        wanted = options["seite"] or ["home", "commercial", "outdoor", "other", "booking", "about", "impressum"]

        manifest_file = self.source / "manifest.json"
        self.manifest = {}
        if manifest_file.exists():
            self.manifest = json.loads(manifest_file.read_text(encoding="utf-8")).get("pages", {})

        self.file_cache = {}
        site = Site.objects.get(is_default_site=True)
        pages = ensure_pages(site, log=self.stdout.write)

        steps = {
            "home": lambda: self.import_home(HomePage.objects.get(pk=site.root_page_id)),
            "commercial": lambda: self.import_gallery(pages.get("commercial"), "commercial"),
            "outdoor": lambda: self.import_gallery(pages.get("outdoor"), "outdoor"),
            "other": lambda: self.import_gallery(pages.get("other"), "other"),
            "booking": lambda: self.import_booking(pages.get("booking")),
            "about": lambda: self.import_about(pages.get("about")),
            "impressum": lambda: self.import_standard(pages.get("impressum"), "impressum"),
        }
        for name in wanted:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{name}"))
            steps[name]()

    def publish(self, page):
        """Wie "Veröffentlichen" im Admin: legt eine Version an und stellt sie live."""
        page.save_revision().publish()
        if hasattr(page, "warm_renditions"):
            self.stdout.write("   erzeuge Bildgrößen ...")
            # Frisch aus der Datenbank laden: Dort stehen die eben gespeicherten Einträge.
            type(page).objects.get(pk=page.pk).warm_renditions()
        self.stdout.write(self.style.SUCCESS("   veröffentlicht"))

    def skip(self, page, key, has_content):
        """Prüft, ob eine Seite bearbeitet werden soll, und meldet den Grund, wenn nicht."""
        if page is None:
            self.stdout.write(self.style.WARNING("   Seite fehlt oder hat einen anderen Typ, übersprungen."))
            return True
        if has_content and not self.force:
            self.stdout.write("   hat schon Inhalt, unverändert (ersetzen mit --neu).")
            return True
        if key not in self.manifest and not (self.source / key).is_dir():
            self.stdout.write(
                self.style.WARNING(f"   wix_import/{key} fehlt. Erst scripts/fetch_wix_images.py ausführen.")
            )
            return True
        return False

    # ------------------------------------------------------------- Quelldaten

    def files(self, key):
        """Wix-ID -> Datei für einen Seitenordner. Die Dateien heißen z. B. 007_c5ec14_<id>.jpg."""
        if key not in self.file_cache:
            found = {}
            folder = self.source / key
            if folder.is_dir():
                for path in sorted(folder.iterdir()):
                    if path.suffix.lower() in IMAGE_SUFFIXES and wix_id(path.stem):
                        found.setdefault(wix_id(path.stem), path)
            self.file_cache[key] = found
        return self.file_cache[key]

    def content(self, key):
        """Inhalt der Seite in Quelltext-Reihenfolge (aus manifest.json), ohne Fußzeilen-Texte."""
        items = self.manifest.get(key, {}).get("content")
        if items is None:
            return None
        cleaned = []
        for item in items:
            if item["type"] == "text":
                if BOILERPLATE.match(item["text"]):
                    continue
                # Der Editor von Wagtail verlangt Zeilenumbrüche in der Schreibweise <br/>.
                item = {**item, "html": re.sub(r"<br\s*/?>", "<br/>", item["html"])}
            cleaned.append(item)
        return cleaned

    def image_entries(self, key):
        """Bilder einer Seite in ihrer Reihenfolge, jedes nur einmal."""
        content = self.content(key)
        if content is not None:
            entries = [item for item in content if item["type"] == "image"]
        else:
            # Älteres Manifest ohne Inhaltsliste, oder gar keins: Reihenfolge der Dateien.
            entries = [
                {"id": item["url"], "found_in": item.get("found_in")}
                for item in self.manifest.get(key, {}).get("items", [])
                if item["type"] == "image" and item.get("found_in") != "data"
            ] or [{"id": path.stem} for path in self.files(key).values()]
        seen, unique = set(), []
        for entry in entries:
            if wix_id(entry["id"]) not in seen:
                seen.add(wix_id(entry["id"]))
                unique.append(entry)
        return unique

    def texts_missing(self, key):
        if self.content(key) is None:
            self.stdout.write(
                self.style.WARNING(
                    "   Keine Texte im Manifest. scripts/fetch_wix_images.py erneut ausführen, "
                    f"dann: import_wix --seite {key} --neu"
                )
            )
            return True
        return False

    # ------------------------------------------------------ Bibliothek füllen

    def collection(self, name):
        existing = Collection.objects.filter(name=name).first()
        return existing or Collection.get_first_root_node().add_child(name=name)

    def get_image(self, path, title, collection, focal_point=None):
        """Gibt das Bild aus der Bibliothek zurück und lädt es bei Bedarf hoch."""
        Image = get_image_model()
        with path.open("rb") as handle:
            image = Image(title=title, collection=collection)
            image.file = ImageFile(handle, name=path.name)
            # Derselbe Inhalt wird nur einmal gespeichert (Vergleich über Prüfsumme).
            image._set_file_hash()
            handle.seek(0)
            existing = Image.objects.filter(file_hash=image.file_hash).first()
            if existing:
                return existing
            if focal_point:
                # Wagtail erwartet den Fokus als Rechteck in Pixeln. Ein kleines
                # Rechteck um den Punkt lässt den Ausschnitt so groß wie möglich.
                image._set_image_file_metadata()
                image.focal_point_x = round(focal_point[0] * image.width)
                image.focal_point_y = round(focal_point[1] * image.height)
                image.focal_point_width = max(1, round(image.width * 0.05))
                image.focal_point_height = max(1, round(image.height * 0.05))
            image.save()
        return image

    def get_video(self, path, title, collection):
        Document = get_document_model()
        with path.open("rb") as handle:
            document = Document(title=title, collection=collection)
            document.file = File(handle, name=path.name)
            document._set_document_file_metadata()
            handle.seek(0)
            existing = Document.objects.filter(file_hash=document.file_hash).first()
            if existing:
                return existing
            document.save()
        return document

    def images(self, key, entries, title, collection):
        """Lädt die genannten Bilder. Gibt (Bilder, fehlende IDs) zurück."""
        files, images, missing = self.files(key), [], []
        for entry in entries:
            path = files.get(wix_id(entry["id"]))
            if path is None:
                missing.append(wix_id(entry["id"]))
                continue
            images.append(
                self.get_image(path, f"{title} {len(images) + 1:02d}", collection, entry.get("focal_point"))
            )
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    f"   {len(missing)} Fotos fehlen in wix_import/{key} und wurden ausgelassen: "
                    + ", ".join(missing)
                )
            )
        return images

    # ------------------------------------------------------------- Startseite

    def import_home(self, home):
        if not (self.source / "home").is_dir():
            self.stdout.write(self.style.WARNING("   wix_import/home fehlt, übersprungen."))
            return
        collection = self.collection("Startseite")
        changed = False
        for relation, model, entries, label in [
            ("top_gallery_images", HomeTopGalleryImage, HOME_TOP, "Oben"),
            ("bottom_gallery_images", HomeBottomGalleryImage, HOME_BOTTOM, "Unten"),
        ]:
            manager = getattr(home, relation)
            if manager.exists() and not self.force:
                self.stdout.write(f"   Galerie {label}: enthält schon {manager.count()} Bilder, unverändert.")
                continue
            images = self.images(
                "home",
                [{"id": wid, "focal_point": focal} for wid, focal in entries],
                f"Startseite {label}",
                collection,
            )
            # Zuweisen ersetzt den bisherigen Inhalt der Galerie.
            setattr(home, relation, [model(image=image, sort_order=n) for n, image in enumerate(images)])
            self.stdout.write(self.style.SUCCESS(f"   Galerie {label}: {len(images)} Bilder"))
            changed = True
        if changed:
            self.publish(home)
        else:
            # Auch ohne Änderung: fehlende Bildgrößen nachziehen (z. B. die der Großansicht).
            self.stdout.write("   erzeuge fehlende Bildgrößen ...")
            home.warm_renditions()

    # ---------------------------------------------------------- Galerie-Seiten

    def import_gallery(self, page, key):
        if self.skip(page, key, page is not None and page.sections.exists()):
            return
        collection = self.collection(page.title)

        # Abschnitte bilden: Jede Überschrift beginnt einen neuen, Absätze und
        # Bilder danach gehören dazu. Ohne Inhaltsliste gibt es einen Abschnitt.
        drafts = []

        def current():
            if not drafts:
                drafts.append({"heading": "", "texts": [], "entries": []})
            return drafts[-1]

        content = self.content(key)
        if content is None:
            current()["entries"] = self.image_entries(key)
        else:
            seen = set()
            for item in content:
                if item["type"] == "text" and item["tag"] in HEADING_TAGS:
                    drafts.append({"heading": item["text"], "texts": [], "entries": []})
                elif item["type"] == "text" and item["tag"] in {"p", "li"}:
                    current()["texts"].append(item["html"])
                elif item["type"] == "image" and wix_id(item["id"]) not in seen:
                    seen.add(wix_id(item["id"]))
                    current()["entries"].append(item)

        # Videos stehen nicht in der Inhaltsliste. Sie kommen in den Abschnitt,
        # dessen Überschrift nach Cinemagramm klingt, sonst in den ersten.
        video_files = sorted((self.source / key).glob("*.mp4")) if (self.source / key).is_dir() else []
        if video_files:
            target = next((d for d in drafts if "cinema" in d["heading"].casefold()), None) or current()
            target["videos"] = video_files

        sections = []
        for draft in drafts:
            images = self.images(key, draft["entries"], page.title, collection)
            videos = [
                self.get_video(path, f"{page.title} Video {n:02d}", collection)
                for n, path in enumerate(draft.get("videos", []), start=1)
            ]
            if not images and not videos:
                if draft["heading"] or draft["texts"]:
                    self.stdout.write(
                        self.style.WARNING(f"   Abschnitt ohne Bilder ausgelassen: {draft['heading'] or '(ohne Überschrift)'}")
                    )
                continue
            section = GallerySection(
                heading=draft["heading"][:120],
                text="".join(f"<p>{text}</p>" for text in draft["texts"]),
                layout=self.layout_for(draft["entries"]),
                sort_order=len(sections),
            )
            section.images = [GallerySectionImage(image=image, sort_order=n) for n, image in enumerate(images)]
            section.videos = [GallerySectionVideo(video=video, sort_order=n) for n, video in enumerate(videos)]
            sections.append(section)
            self.stdout.write(
                self.style.SUCCESS(
                    f"   Abschnitt {section.heading or '(ohne Überschrift)'}: {len(images)} Bilder, "
                    f"{len(videos)} Videos, Darstellung {section.get_layout_display()}"
                )
            )

        page.sections = sections
        self.publish(page)

    @staticmethod
    def layout_for(entries):
        """Wählt die Darstellung nach den Kacheln der Wix-Seite: schmale Hochformate werden zur Bildreihe."""
        tiles = [(e["width"], e["height"]) for e in entries if e.get("width") and e.get("height")]
        tall = [tile for tile in tiles if tile[1] / tile[0] >= 2]
        if not tiles or len(tall) < len(tiles) / 2:
            return "grid"
        average_width = sum(width for width, _height in tall) / len(tall)
        return "strip_large" if average_width >= 140 else "strip_small"

    # ------------------------------------------------------------------ Booking

    def import_booking(self, page):
        if self.skip(page, "booking", page is not None and (page.intro or page.strip_images.exists())):
            return
        content = self.content("booking")
        if not self.texts_missing("booking"):
            page.intro = "".join(
                f"<p>{item['html']}</p>"
                for item in content
                if item["type"] == "text"
                and item["tag"] in HEADING_TAGS | {"p"}
                and not CONTACT_LINE.search(item["text"])
            )
            fields = [item["label"] or item["name"] for item in content if item["type"] == "field"]
            if fields:
                self.stdout.write(f"   Formularfelder bei Wix: {', '.join(fields)}")
        images = self.images("booking", self.image_entries("booking"), page.title, self.collection(page.title))
        page.strip_images = [BookingStripImage(image=image, sort_order=n) for n, image in enumerate(images)]
        self.stdout.write(self.style.SUCCESS(f"   Einleitung {'ja' if page.intro else 'nein'}, {len(images)} Bilder"))
        self.publish(page)

    # -------------------------------------------------------------------- About

    def import_about(self, page):
        if self.skip(page, "about", page is not None and (page.body or page.image_id)):
            return
        content = self.content("about")
        if not self.texts_missing("about"):
            page.body = "".join(
                f"<p>{item['html']}</p>"
                for item in content
                if item["type"] == "text" and item["tag"] in HEADING_TAGS | {"p"}
            )
        images = self.images("about", self.image_entries("about")[:1], page.title, self.collection(page.title))
        page.image = images[0] if images else None
        self.stdout.write(
            self.style.SUCCESS(f"   Text {'ja' if page.body else 'nein'}, Porträt {'ja' if images else 'nein'}")
        )
        self.publish(page)

    # ---------------------------------------------------------------- Impressum

    def import_standard(self, page, key):
        if self.skip(page, key, page is not None and bool(page.body)):
            return
        if self.texts_missing(key):
            return
        parts, in_list = [], False
        for item in self.content(key):
            if item["type"] != "text" or item["tag"] in {"label", "button"}:
                continue
            if item["tag"] == "li":
                if not in_list:
                    parts.append("<ul>")
                    in_list = True
                parts.append(f"<li>{item['html']}</li>")
                continue
            if in_list:
                parts.append("</ul>")
                in_list = False
            if item["tag"] in HEADING_TAGS:
                # Die Überschrift, die nur den Seitentitel wiederholt, steht schon oben.
                if not parts and item["text"].casefold() == page.title.casefold():
                    continue
                level = "h2" if item["tag"] in {"h1", "h2"} else "h3"
                parts.append(f"<{level}>{item['text']}</{level}>")
            else:
                parts.append(f"<p>{item['html']}</p>")
        if in_list:
            parts.append("</ul>")
        page.body = "".join(parts)
        self.stdout.write(self.style.SUCCESS(f"   {len(parts)} Textblöcke"))
        self.publish(page)
