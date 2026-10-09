from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, MultipleChooserPanel
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page


class HomePage(Page):
    """Startseite mit zwei waagerecht scrollenden Galerien aus hochkant beschnittenen Bildern."""

    # Bildgrößen, die das Template anfordert (home/includes/gallery_strip.html).
    # Hier noch einmal aufgeführt, damit der Import sie vorab erzeugen kann.
    TOP_RENDITIONS = ["fill-160x456|format-webp", "fill-320x912|format-webp"]
    BOTTOM_RENDITIONS = [
        "fill-101x289|format-webp",
        "fill-202x578|format-webp",
        "fill-303x867|format-webp",
    ]

    content_panels = Page.content_panels + [
        MultipleChooserPanel(
            "top_gallery_images",
            heading="Obere Galerie (große Bilder)",
            label="Bild",
            chooser_field_name="image",
        ),
        MultipleChooserPanel(
            "bottom_gallery_images",
            heading="Untere Galerie (kleine Bilder)",
            label="Bild",
            chooser_field_name="image",
        ),
    ]

    class Meta:
        verbose_name = "Startseite"
        verbose_name_plural = "Startseiten"

    def warm_renditions(self):
        """Erzeugt alle Bildgrößen der Galerien, damit der erste Seitenaufruf nicht darauf wartet."""
        for item in self.top_gallery_images.select_related("image"):
            item.image.get_renditions(*self.TOP_RENDITIONS)
        for item in self.bottom_gallery_images.select_related("image"):
            item.image.get_renditions(*self.BOTTOM_RENDITIONS)


class GalleryImage(Orderable):
    """Ein Bild in einer Galerie. Der Bildausschnitt folgt dem Fokuspunkt des Bildes."""

    image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Bild",
        on_delete=models.CASCADE,
        related_name="+",
    )

    panels = [FieldPanel("image")]

    class Meta(Orderable.Meta):
        abstract = True


class HomeTopGalleryImage(GalleryImage):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="top_gallery_images")


class HomeBottomGalleryImage(GalleryImage):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="bottom_gallery_images")
