from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultipleChooserPanel
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page

from core import images as image_specs

# Erlaubte Formatierungen in kurzen Texten: nur das Nötigste.
SIMPLE_FEATURES = ["bold", "italic", "link"]
# In langen Texten (Impressum) zusätzlich Überschriften und Listen.
LONG_FEATURES = ["h2", "h3", "bold", "italic", "link", "ol", "ul"]


class PhotoLibraryPage(Page):
    """Foto-Bibliothek: alle Fotos auf einer Seite, oben Filter nach Tags.

    Die Tags stehen am Bild selbst (Bilder -> Bild bearbeiten -> Tags). Welche
    Tags als Filter erscheinen und in welcher Reihenfolge, legt die Seite fest.
    Ohne aktiven Filter zeigt sie alle Fotos gemischt.
    """

    intro = RichTextField("Einleitung", blank=True, features=SIMPLE_FEATURES)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel(
            "filters",
            heading="Filter",
            label="Filter",
            help_text="Tags, nach denen Besucher filtern können. Ein Bild erscheint unter einem Filter, wenn es diesen Tag trägt.",
        ),
        MultipleChooserPanel("photos", heading="Fotos", label="Foto", chooser_field_name="image"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Foto-Bibliothek"
        verbose_name_plural = "Foto-Bibliotheken"

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        filters = list(self.filters.select_related("tag"))
        photos = list(image_specs.with_renditions(self.photos.all()).prefetch_related("image__tags"))
        filter_slugs = {f.tag.slug for f in filters}
        for photo in photos:
            photo.tag_slugs = sorted({tag.slug for tag in photo.image.tags.all()} & filter_slugs)

        # Mit ?tag=... funktioniert der Filter auch ohne JavaScript und als teilbarer Link.
        active = request.GET.get("tag", "")
        if active not in filter_slugs:
            active = ""
        for photo in photos:
            photo.visible = not active or active in photo.tag_slugs

        visible_count = sum(photo.visible for photo in photos)
        context.update(filters=filters, photos=photos, active_filter=active, visible_count=visible_count)
        return context

    def warm_renditions(self):
        image_specs.warm([item.image for item in self.photos.select_related("image")], image_specs.GRID)


class LibraryFilter(Orderable):
    page = ParentalKey(PhotoLibraryPage, on_delete=models.CASCADE, related_name="filters")
    tag = models.ForeignKey("taggit.Tag", verbose_name="Tag", on_delete=models.CASCADE, related_name="+")
    label = models.CharField(
        "Beschriftung", max_length=40, blank=True, help_text="Leer lassen, um den Namen des Tags zu zeigen."
    )

    panels = [FieldPanel("tag"), FieldPanel("label")]

    class Meta(Orderable.Meta):
        verbose_name = "Filter"
        verbose_name_plural = "Filter"

    @property
    def name(self):
        return self.label or self.tag.name


class LibraryPhoto(Orderable):
    page = ParentalKey(PhotoLibraryPage, on_delete=models.CASCADE, related_name="photos")
    image = models.ForeignKey(
        get_image_model_string(), verbose_name="Foto", on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("image")]


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
