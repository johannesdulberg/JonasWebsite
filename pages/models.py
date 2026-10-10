from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultipleChooserPanel
from wagtail.documents import get_document_model_string
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page

from core import images as image_specs

# Erlaubte Formatierungen in kurzen Texten: nur das Nötigste.
SIMPLE_FEATURES = ["bold", "italic", "link"]
# In langen Texten (Impressum) zusätzlich Überschriften und Listen.
LONG_FEATURES = ["h2", "h3", "bold", "italic", "link", "ol", "ul"]


class GalleryPage(Page):
    """Seite aus einem oder mehreren Bildabschnitten (Commercial, Outdoor, Other)."""

    intro = RichTextField("Einleitung", blank=True, features=SIMPLE_FEATURES)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel("sections", heading="Abschnitte", label="Abschnitt"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Galerie-Seite"
        verbose_name_plural = "Galerie-Seiten"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["sections"] = self.sections.prefetch_related(
            models.Prefetch(
                "images", queryset=image_specs.with_renditions(GallerySectionImage.objects.all())
            ),
            models.Prefetch("videos", queryset=GallerySectionVideo.objects.select_related("video")),
        )
        return context

    def warm_renditions(self):
        for section in self.sections.all():
            specs = image_specs.BY_LAYOUT[section.layout]
            image_specs.warm([item.image for item in section.images.select_related("image")], specs)


class GallerySection(ClusterableModel, Orderable):
    """Ein Abschnitt einer Galerie-Seite: optionale Überschrift und Text, dann Bilder und/oder Videos."""

    LAYOUT_CHOICES = [
        ("grid", "Raster (ganze Bilder, gleich hohe Zeilen)"),
        ("strip_large", "Bildreihe zum Blättern, groß (Hochformat-Ausschnitte)"),
        ("strip_small", "Bildreihe zum Blättern, klein (Hochformat-Ausschnitte)"),
    ]

    page = ParentalKey(GalleryPage, on_delete=models.CASCADE, related_name="sections")
    heading = models.CharField("Überschrift", max_length=120, blank=True)
    text = RichTextField("Text", blank=True, features=SIMPLE_FEATURES)
    layout = models.CharField("Darstellung", max_length=20, choices=LAYOUT_CHOICES, default="grid")

    panels = [
        FieldPanel("heading"),
        FieldPanel("text"),
        FieldPanel("layout"),
        MultipleChooserPanel("images", heading="Bilder", label="Bild", chooser_field_name="image"),
        MultipleChooserPanel("videos", heading="Videos", label="Video", chooser_field_name="video"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Abschnitt"
        verbose_name_plural = "Abschnitte"


class GallerySectionImage(Orderable):
    section = ParentalKey(GallerySection, on_delete=models.CASCADE, related_name="images")
    image = models.ForeignKey(
        get_image_model_string(), verbose_name="Bild", on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("image")]


class GallerySectionVideo(Orderable):
    """Kurzes Video ohne Ton, das in Schleife läuft (Cinemagramm). Als Dokument hochgeladen (MP4)."""

    section = ParentalKey(GallerySection, on_delete=models.CASCADE, related_name="videos")
    video = models.ForeignKey(
        get_document_model_string(),
        verbose_name="Video (MP4)",
        on_delete=models.CASCADE,
        related_name="+",
    )

    panels = [FieldPanel("video")]


class AboutPage(Page):
    """Vorstellung mit Text und Porträt."""

    image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Porträt",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    body = RichTextField("Text", blank=True, features=SIMPLE_FEATURES)

    content_panels = Page.content_panels + [FieldPanel("image"), FieldPanel("body")]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "About-Seite"
        verbose_name_plural = "About-Seiten"

    def warm_renditions(self):
        if self.image:
            self.image.get_renditions(*image_specs.PORTRAIT)


class BookingPage(Page):
    """Kontaktseite: Einleitung, eine Bildreihe, Kontaktdaten und ein Formular.

    Das Formular wird angezeigt, verschickt aber noch nichts (siehe TODO.md).
    E-Mail und Telefon kommen aus Einstellungen -> Kopf- und Fußzeile.
    """

    intro = RichTextField("Einleitung", blank=True, features=SIMPLE_FEATURES)
    contact_heading = models.CharField("Überschrift Kontakt", max_length=80, default="Kontakt")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultipleChooserPanel(
            "strip_images", heading="Bildreihe", label="Bild", chooser_field_name="image"
        ),
        FieldPanel("contact_heading"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Booking-Seite"
        verbose_name_plural = "Booking-Seiten"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["strip_images"] = image_specs.with_renditions(self.strip_images.all())
        return context

    def warm_renditions(self):
        image_specs.warm(
            [item.image for item in self.strip_images.select_related("image")],
            image_specs.STRIP_SMALL,
        )


class BookingStripImage(Orderable):
    page = ParentalKey(BookingPage, on_delete=models.CASCADE, related_name="strip_images")
    image = models.ForeignKey(
        get_image_model_string(), verbose_name="Bild", on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("image")]


class StandardPage(Page):
    """Reine Textseite, zum Beispiel Impressum und Datenschutz."""

    body = RichTextField("Text", blank=True, features=LONG_FEATURES)

    content_panels = Page.content_panels + [FieldPanel("body")]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Textseite"
        verbose_name_plural = "Textseiten"
