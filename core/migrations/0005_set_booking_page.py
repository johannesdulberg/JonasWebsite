"""Verknüpft den Termin-Knopf mit der vorhandenen Seite "booking".

Eigene Migration, weil Postgres Schemaänderung und Datenänderung an derselben
Tabelle nicht in einem Schritt mag.
"""

from django.db import migrations


def set_booking_page(apps, schema_editor):
    SiteSettings = apps.get_model("core", "SiteSettings")
    Page = apps.get_model("wagtailcore", "Page")
    for settings in SiteSettings.objects.filter(booking_page__isnull=True).select_related("site__root_page"):
        root = settings.site.root_page
        page = Page.objects.filter(
            path__startswith=root.path, depth=root.depth + 1, slug="booking"
        ).first()
        if page is not None:
            settings.booking_page = page
            settings.save(update_fields=["booking_page"])


class Migration(migrations.Migration):
    dependencies = [("core", "0004_booking_button")]

    operations = [migrations.RunPython(set_booking_page, migrations.RunPython.noop)]
