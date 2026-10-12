"""Erster Schritt beim Umbau auf die Foto-Bibliothek: alte Galerie-Seiten entfernen.

Eigene Migration, weil Postgres Daten löschen und Tabellen umbauen nicht in
derselben Transaktion erlaubt ("pending trigger events").
"""

from django.db import migrations

def delete_gallery_pages(apps, schema_editor):
    """Entfernt die alten Galerie-Seiten (Commercial, Outdoor, Other) aus dem Seitenbaum.

    Ihre Fotos bleiben in der Bildbibliothek. import_wix übernimmt sie mit Tags
    in die Foto-Bibliothek.
    """
    ContentType = apps.get_model("contenttypes", "ContentType")
    Page = apps.get_model("wagtailcore", "Page")
    Revision = apps.get_model("wagtailcore", "Revision")
    content_type = ContentType.objects.filter(app_label="pages", model="gallerypage").first()
    if content_type is None:
        return
    pages = list(Page.objects.filter(content_type=content_type))
    parent_paths = {page.path[: -4] for page in pages}
    Revision.objects.filter(content_type=content_type).delete()
    for page in pages:
        # Seite und ggf. Unterseiten (es gab keine) samt Galerie-Daten löschen.
        Page.objects.filter(path__startswith=page.path).delete()
    # Den Zähler der Elternseiten im Seitenbaum korrigieren.
    for path in parent_paths:
        for parent in Page.objects.filter(path=path):
            parent.numchild = Page.objects.filter(path__startswith=path, depth=parent.depth + 1).count()
            parent.save(update_fields=["numchild"])


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0001_initial"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]

    operations = [
        migrations.RunPython(delete_gallery_pages, migrations.RunPython.noop),
    ]
