"""Übernimmt die von der Wix-Seite geladenen Fotos in Wagtail.

    docker compose exec web python manage.py import_wix

Voraussetzung: Der Ordner wix_import/ ist gefüllt (scripts/fetch_wix_images.py).

Der Befehl tut dasselbe wie jemand im Admin: Er lädt die Fotos in die
Bildbibliothek (Sammlung "Startseite"), setzt den Fokuspunkt und hängt sie in
der richtigen Reihenfolge an die beiden Galerien der Startseite. Danach lässt
sich alles im Admin weiter bearbeiten.

Eine Galerie, die schon Bilder enthält, bleibt unverändert. Mit --neu wird sie
geleert und neu befüllt (die Bilder in der Bibliothek bleiben erhalten).
"""

from pathlib import Path

from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from wagtail.images import get_image_model
from wagtail.models import Collection, Site

from home.models import HomeBottomGalleryImage, HomePage, HomeTopGalleryImage

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

COLLECTION_NAME = "Startseite"


class Command(BaseCommand):
    help = "Übernimmt die Fotos aus wix_import/ in die Bildbibliothek und die Galerien der Startseite."

    def add_arguments(self, parser):
        parser.add_argument(
            "--neu",
            action="store_true",
            help="Galerien leeren und neu befüllen, auch wenn sie schon Bilder enthalten.",
        )
        parser.add_argument(
            "--quelle",
            default=str(Path(settings.BASE_DIR) / "wix_import"),
            help="Ordner mit den heruntergeladenen Fotos (Standard: wix_import im Projekt).",
        )

    def handle(self, *args, **options):
        source = Path(options["quelle"]) / "home"
        if not source.is_dir():
            raise CommandError(
                f"{source} fehlt. Zuerst die Fotos laden: python scripts/fetch_wix_images.py"
            )

        # Wix-ID -> Datei. Die Dateien heißen z. B. 007_c5ec14_<id>.jpg.
        self.files = {}
        for path in sorted(source.iterdir()):
            parts = path.stem.split("_")
            if len(parts) == 3 and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                self.files.setdefault(parts[2], path)

        self.collection = self.get_collection()
        home = HomePage.objects.get(pk=Site.objects.get(is_default_site=True).root_page_id)

        changed = False
        changed |= self.fill(home, "top_gallery_images", HomeTopGalleryImage, HOME_TOP, "Oben", options["neu"])
        changed |= self.fill(
            home, "bottom_gallery_images", HomeBottomGalleryImage, HOME_BOTTOM, "Unten", options["neu"]
        )

        if changed:
            # Wie "Veröffentlichen" im Admin: legt eine Version an und stellt sie live.
            home.save_revision().publish()
            self.stdout.write("Erzeuge Bildgrößen (dauert beim ersten Mal einen Moment) ...")
            home.warm_renditions()
            self.stdout.write(self.style.SUCCESS("Startseite veröffentlicht."))
        else:
            self.stdout.write("Nichts zu tun. Mit --neu werden die Galerien neu befüllt.")

    def get_collection(self):
        existing = Collection.objects.filter(name=COLLECTION_NAME).first()
        return existing or Collection.get_first_root_node().add_child(name=COLLECTION_NAME)

    def fill(self, home, relation, model, entries, label, force):
        """Befüllt eine Galerie. Gibt zurück, ob sich etwas geändert hat."""
        manager = getattr(home, relation)
        if manager.exists() and not force:
            self.stdout.write(f"Galerie {label}: enthält schon {manager.count()} Bilder, unverändert.")
            return False

        items, missing = [], []
        for position, (wix_id, focal_point) in enumerate(entries, start=1):
            path = self.files.get(wix_id)
            if path is None:
                missing.append(wix_id)
                continue
            image = self.get_image(path, f"Startseite {label} {position:02d}", focal_point)
            items.append(model(image=image, sort_order=len(items)))

        # Zuweisen ersetzt den bisherigen Inhalt der Galerie.
        setattr(home, relation, items)
        self.stdout.write(self.style.SUCCESS(f"Galerie {label}: {len(items)} Bilder"))
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    f"   {len(missing)} Fotos fehlen in wix_import/home und wurden ausgelassen: "
                    + ", ".join(missing)
                )
            )
        return True

    def get_image(self, path, title, focal_point):
        """Gibt das Bild aus der Bibliothek zurück und lädt es bei Bedarf hoch."""
        Image = get_image_model()
        with path.open("rb") as handle:
            image = Image(title=title, collection=self.collection)
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
