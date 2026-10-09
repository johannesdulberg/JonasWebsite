from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.images.models import AbstractImage, AbstractRendition, Image
from wagtail.models import Orderable

from .social_icons import SOCIAL_ICONS


class CustomImage(AbstractImage):
    """Eigenes Bildmodell statt des eingebauten von Wagtail.

    Verhält sich bisher identisch. Der Zweck: Später lassen sich Felder ergänzen
    (z. B. Bildnachweis), ohne alle Bilder umziehen zu müssen. Der Wechsel des
    Bildmodells ist nachträglich aufwendig, am Anfang kostet er nichts.
    """

    admin_form_fields = Image.admin_form_fields

    class Meta(AbstractImage.Meta):
        verbose_name = "Bild"
        verbose_name_plural = "Bilder"


class CustomRendition(AbstractRendition):
    """Die von Wagtail erzeugten Größen und Formate eines Bildes."""

    image = models.ForeignKey(CustomImage, on_delete=models.CASCADE, related_name="renditions")

    class Meta:
        unique_together = (("image", "filter_spec", "focal_point_key"),)


@register_setting(icon="cog")
class SiteSettings(BaseSiteSetting, ClusterableModel):
    """Alles, was in Kopf- und Fußzeile steht und nicht aus dem Seitenbaum kommt.

    Im Admin unter Einstellungen -> Kopf- und Fußzeile.
    """

    brand_name = models.CharField("Name", max_length=100, default="Jonas Dülberg")
    tagline = models.CharField(
        "Untertitel", max_length=150, blank=True, default="Outdoor- und Werbefotografie"
    )

    contact_name = models.CharField("Name / Firma", max_length=100, blank=True)
    street = models.CharField("Straße und Hausnummer", max_length=100, blank=True)
    postal_code_city = models.CharField("PLZ und Ort", max_length=100, blank=True)
    email = models.EmailField("E-Mail", blank=True)
    phone = models.CharField("Telefon", max_length=50, blank=True)

    legal_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Seite für Impressum / Datenschutz",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    legal_link_text = models.CharField(
        "Linktext", max_length=100, default="Impressum / Datenschutz"
    )

    footer_download = models.ForeignKey(
        "wagtaildocs.Document",
        verbose_name="Datei",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    footer_download_text = models.CharField(
        "Text zum Download",
        max_length=150,
        blank=True,
        help_text='Zum Beispiel: Handy-Wallpaper "Waves" (kostenlos)',
    )

    panels = [
        MultiFieldPanel(
            [FieldPanel("brand_name"), FieldPanel("tagline")],
            heading="Kopfzeile",
        ),
        MultiFieldPanel(
            [
                FieldPanel("contact_name"),
                FieldPanel("street"),
                FieldPanel("postal_code_city"),
                FieldPanel("email"),
                FieldPanel("phone"),
            ],
            heading="Kontakt in der Fußzeile",
        ),
        InlinePanel("social_links", heading="Social Media", label="Link"),
        MultiFieldPanel(
            [FieldPanel("legal_page"), FieldPanel("legal_link_text")],
            heading="Impressum / Datenschutz",
        ),
        MultiFieldPanel(
            [FieldPanel("footer_download"), FieldPanel("footer_download_text")],
            heading="Download in der Fußzeile",
        ),
    ]

    class Meta:
        verbose_name = "Kopf- und Fußzeile"


class SocialLink(Orderable):
    PLATFORM_CHOICES = [(key, name) for key, (name, _path) in SOCIAL_ICONS.items()]

    settings = ParentalKey(SiteSettings, on_delete=models.CASCADE, related_name="social_links")
    platform = models.CharField(
        "Plattform",
        max_length=30,
        blank=True,
        choices=PLATFORM_CHOICES,
        help_text="Mit Plattform erscheint das passende Icon. Leer lassen für einen Textlink.",
    )
    label = models.CharField(
        "Bezeichnung",
        max_length=50,
        blank=True,
        help_text="Nur nötig ohne Plattform, zum Beispiel: LinkedIn",
    )
    url = models.URLField("Adresse")

    panels = [FieldPanel("platform"), FieldPanel("url"), FieldPanel("label")]

    class Meta(Orderable.Meta):
        verbose_name = "Social-Media-Link"
        verbose_name_plural = "Social-Media-Links"

    def clean(self):
        super().clean()
        if not self.platform and not self.label:
            raise ValidationError({"label": "Ohne Plattform braucht der Link eine Bezeichnung."})

    @property
    def name(self):
        """Name für Textlink und Screenreader."""
        return self.label or self.get_platform_display()

    @property
    def icon_path(self):
        """SVG-Pfad des Icons oder leer, wenn der Link als Text erscheinen soll."""
        return SOCIAL_ICONS[self.platform][1] if self.platform in SOCIAL_ICONS else ""
