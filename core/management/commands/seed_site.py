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

        # Erst hier importieren: pages hängt von core ab, nicht umgekehrt.
        from pages.setup import ensure_pages

        pages = ensure_pages(site, log=self.stdout.write)

        settings = SiteSettings.for_site(site)

        for field, value in SETTINGS.items():
            if not getattr(settings, field):
                setattr(settings, field, value)

        if settings.legal_page is None and "impressum" in pages:
            settings.legal_page = Page.objects.get(pk=pages["impressum"].pk)

        settings.save()

        if not settings.social_links.exists():
            for platform, url in SOCIAL_LINKS:
                SocialLink.objects.create(settings=settings, platform=platform, url=url)
            self.stdout.write(self.style.SUCCESS("Social-Media-Links angelegt"))

        self.stdout.write(self.style.SUCCESS("Kontakt, Impressum-Link und Social Media sind eingetragen."))

        # Das Wallpaper kommt zuletzt: Scheitert der Download oder das Speichern,
        # ist alles andere schon eingetragen.
        if settings.footer_download is None:
            wallpaper = self.get_wallpaper()
            if wallpaper:
                settings.footer_download = wallpaper
                settings.save()
                self.stdout.write(self.style.SUCCESS("Wallpaper als Download eingehängt"))

    def get_wallpaper(self):
        """Gibt das Wallpaper als Dokument zurück, lädt es bei Bedarf von der Wix-Seite."""
        Document = get_document_model()
        existing = Document.objects.filter(title=WALLPAPER_TITLE).first()
        if existing:
            return existing
        try:
            data = download(WALLPAPER_URL)
            document = Document.objects.create(
                title=WALLPAPER_TITLE, file=ContentFile(data, name=WALLPAPER_FILENAME)
            )
        except Exception as error:
            self.stdout.write(
                self.style.WARNING(
                    f"Wallpaper nicht eingehängt ({type(error).__name__}: {error}). Später erneut "
                    "ausführen oder die Datei im Admin unter Dokumente hochladen."
                )
            )
            return None
        return document
