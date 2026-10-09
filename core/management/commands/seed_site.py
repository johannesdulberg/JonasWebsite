"""Erstbefüllung: legt die Seiten der bisherigen Wix-Seite an und füllt Kopf- und Fußzeile.

    docker compose exec web python manage.py seed_site

Der Befehl kann mehrfach laufen. Er legt nur an, was fehlt, und überschreibt
keine Felder, die im Admin schon ausgefüllt wurden.
"""

import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from wagtail.documents import get_document_model
from wagtail.models import Page, Site

from core.models import SiteSettings, SocialLink
from home.models import HomePage

# (Titel, Slug, im Menü anzeigen). Reihenfolge = Reihenfolge im Menü.
PAGES = [
    ("Commercial", "commercial", True),
    ("Outdoor", "outdoor", True),
    ("Other", "other", True),
    ("Booking", "booking", True),
    ("About", "about", True),
    ("Impressum", "impressum", False),
]

# Angaben aus Fußzeile und Impressum der bisherigen Seite.
SETTINGS = {
    "contact_name": "Jonas Dülberg",
    "street": "Kampstraße 12",
    "postal_code_city": "59494 Soest",
    "email": "jonasduelberg@live.com",
    "phone": "+4915783884044",
    "footer_download_text": 'Handy Wallpaper "Waves" zum Download (free).',
}

SOCIAL_LINKS = [
    ("instagram", "https://instagram.com/north.johnny"),
    ("tiktok", "https://www.tiktok.com/@north.johnny"),
]

WALLPAPER_TITLE = "Waves Wallpaper"
WALLPAPER_FILENAME = "waves-wallpaper.zip"
WALLPAPER_URL = (
    "https://www.jonasduelberg.com/_files/archives/"
    "c5ec14_f1dcfcdafe114d8a9cda7ad676e4761b.zip?dn=Waves%20Wallpaper.zip"
)


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


class Command(BaseCommand):
    help = "Legt Seiten, Kopf- und Fußzeile nach Vorbild der bisherigen Wix-Seite an."

    def handle(self, *args, **options):
        site = Site.objects.get(is_default_site=True)
        home = site.root_page

        for title, slug, in_menu in PAGES:
            if home.get_children().filter(slug=slug).exists():
                self.stdout.write(f"Seite vorhanden: {title}")
                continue
            # Vorerst der einzige vorhandene Seitentyp. Sobald es eigene Typen für
            # Galerie, Booking und About gibt, werden diese Platzhalter ersetzt.
            home.add_child(instance=HomePage(title=title, slug=slug, show_in_menus=in_menu))
            self.stdout.write(self.style.SUCCESS(f"Seite angelegt: {title}"))

        settings = SiteSettings.for_site(site)

        for field, value in SETTINGS.items():
            if not getattr(settings, field):
                setattr(settings, field, value)

        if settings.legal_page is None:
            settings.legal_page = Page.objects.get(pk=home.get_children().get(slug="impressum").pk)

        if settings.footer_download is None:
            settings.footer_download = self.get_wallpaper()

        settings.save()

        if not settings.social_links.exists():
            for platform, url in SOCIAL_LINKS:
                SocialLink.objects.create(settings=settings, platform=platform, url=url)
            self.stdout.write(self.style.SUCCESS("Social-Media-Links angelegt"))

        self.stdout.write(self.style.SUCCESS("Kopf- und Fußzeile sind befüllt."))

    def get_wallpaper(self):
        """Gibt das Wallpaper als Dokument zurück, lädt es bei Bedarf von der Wix-Seite."""
        Document = get_document_model()
        existing = Document.objects.filter(title=WALLPAPER_TITLE).first()
        if existing:
            return existing
        try:
            data = download(WALLPAPER_URL)
        except Exception as error:
            self.stdout.write(
                self.style.WARNING(
                    f"Wallpaper nicht geladen ({error}). Später erneut ausführen "
                    "oder die Datei im Admin unter Dokumente hochladen."
                )
            )
            return None
        document = Document.objects.create(
            title=WALLPAPER_TITLE, file=ContentFile(data, name=WALLPAPER_FILENAME)
        )
        self.stdout.write(self.style.SUCCESS("Wallpaper heruntergeladen"))
        return document
