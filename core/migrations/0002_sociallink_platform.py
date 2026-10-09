from django.db import migrations, models

from core.social_icons import SOCIAL_ICONS


def set_platform_from_label(apps, schema_editor):
    """Bestehende Textlinks wie "Instagram" bekommen die passende Plattform."""
    SocialLink = apps.get_model("core", "SocialLink")
    by_name = {name.lower(): key for key, (name, _path) in SOCIAL_ICONS.items()}
    for link in SocialLink.objects.all():
        key = by_name.get(link.label.strip().lower())
        if key:
            link.platform = key
            link.label = ""
            link.save(update_fields=["platform", "label"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sociallink",
            name="platform",
            field=models.CharField(
                blank=True,
                choices=[(key, name) for key, (name, _path) in SOCIAL_ICONS.items()],
                help_text="Mit Plattform erscheint das passende Icon. Leer lassen für einen Textlink.",
                max_length=30,
                verbose_name="Plattform",
            ),
        ),
        migrations.AlterField(
            model_name="sociallink",
            name="label",
            field=models.CharField(
                blank=True,
                help_text="Nur nötig ohne Plattform, zum Beispiel: LinkedIn",
                max_length=50,
                verbose_name="Bezeichnung",
            ),
        ),
        migrations.RunPython(set_platform_from_label, migrations.RunPython.noop),
    ]
