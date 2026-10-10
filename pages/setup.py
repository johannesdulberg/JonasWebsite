"""Die Seitenstruktur der bisherigen Wix-Seite: welche Seiten es gibt und von welchem Typ.

Wird von seed_site (Grundgerüst) und import_wix (Inhalte) benutzt.
"""

from wagtail.models import Page

from core.models import SiteSettings
from home.models import HomePage

from .models import AboutPage, BookingPage, GalleryPage, StandardPage

# (Titel, Slug, im Menü anzeigen, Seitentyp). Reihenfolge = Reihenfolge im Menü.
PAGES = [
    ("Commercial", "commercial", True, GalleryPage),
    ("Outdoor", "outdoor", True, GalleryPage),
    ("Other", "other", True, GalleryPage),
    ("Booking", "booking", True, BookingPage),
    ("About", "about", True, AboutPage),
    ("Impressum", "impressum", False, StandardPage),
]


def ensure_pages(site, log=lambda message: None):
    """Sorgt dafür, dass alle Seiten mit dem richtigen Typ existieren.

    Gibt ein Wörterbuch Slug -> Seite zurück. Platzhalter aus der Anfangszeit
    (als es nur den Typ Startseite gab) werden durch den richtigen Typ ersetzt.
    Seiten, die schon den richtigen Typ haben, bleiben unangetastet.
    """
    home = site.root_page
    result = {}
    replaced = False

    for title, slug, in_menu, model in PAGES:
        existing = home.get_children().filter(slug=slug).first()
        if existing is not None:
            specific = existing.specific
            if isinstance(specific, model):
                result[slug] = specific
                continue
            if not isinstance(specific, HomePage):
                # Jemand hat hier bewusst etwas anderes angelegt: nicht anfassen.
                log(f"Seite /{slug}/ hat einen anderen Typ ({specific._meta.verbose_name}), übersprungen.")
                continue
            title, in_menu = existing.title, existing.show_in_menus
            existing.delete()
            replaced = True
            log(f"Platzhalter ersetzt: {title}")
        else:
            log(f"Seite angelegt: {title}")

        # Nach dem Löschen ist die im Speicher gehaltene Elternseite veraltet.
        home = Page.objects.get(pk=home.pk)
        result[slug] = home.add_child(instance=model(title=title, slug=slug, show_in_menus=in_menu))

    if replaced:
        # Ersetzte Seiten hängen am Ende. Reihenfolge wiederherstellen: der Reihe
        # nach ans Ende schieben. Seiten, die nicht in der Liste stehen, bleiben davor.
        for _title, slug, _in_menu, _model in PAGES:
            if slug in result:
                Page.objects.get(pk=result[slug].pk).move(Page.objects.get(pk=home.pk), pos="last-child")
                result[slug] = result[slug].__class__.objects.get(pk=result[slug].pk)

    # Der Impressum-Link der Fußzeile zeigte ggf. auf den gelöschten Platzhalter.
    settings = SiteSettings.for_site(site)
    if settings.legal_page_id is None and "impressum" in result:
        settings.legal_page = Page.objects.get(pk=result["impressum"].pk)
        settings.save()

    return result
