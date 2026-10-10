from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, MultipleChooserPanel
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page

from core import images as image_specs


class HomePage(Page):
    """Startseite mit zwei waagerecht scrollenden Galerien aus hochkant beschnittenen Bildern."""

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

    # Es gibt genau eine Startseite, direkt unter der Wurzel des Seitenbaums.
    parent_page_types = ["wagtailcore.Page"]

    class Meta:
        verbose_name = "Startseite"
        verbose_name_plural = "Startseiten"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["top"] = image_specs.with_renditions(self.top_gallery_images.all())
        context["bottom"] = image_specs.with_renditions(self.bottom_gallery_images.all())
        return context

    def warm_renditions(self):
        """Erzeugt alle Bildgrößen der Galerien, damit der erste Seitenaufruf nicht darauf wartet."""
        image_specs.warm(
            [item.image for item in self.top_gallery_images.select_related("image")],
            image_specs.STRIP_LARGE,
        )
        image_specs.warm(
            [item.image for item in self.bottom_gallery_images.select_related("image")],
            image_specs.STRIP_SMALL,
        )


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
