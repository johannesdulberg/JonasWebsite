from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Orderable


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
    settings = ParentalKey(SiteSettings, on_delete=models.CASCADE, related_name="social_links")
    label = models.CharField("Bezeichnung", max_length=50, help_text="Zum Beispiel: Instagram")
    url = models.URLField("Adresse")

    panels = [FieldPanel("label"), FieldPanel("url")]

    class Meta(Orderable.Meta):
        verbose_name = "Social-Media-Link"
        verbose_name_plural = "Social-Media-Links"
