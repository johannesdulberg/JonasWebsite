"""Bildgrößen an einer Stelle.

Die Templates fordern diese Größen an (config/templates/includes/gallery_*.html).
Hier stehen sie noch einmal, damit der Import sie vorab erzeugen kann und der
erste Seitenaufruf nicht darauf warten muss. Wer eine Größe im Template ändert,
ändert sie auch hier.
"""

# Großansicht nach Klick
LIGHTBOX = ["max-2000x2000|format-webp"]

# Bildreihen im Hochformat (Ausschnitt folgt dem Fokuspunkt)
STRIP_LARGE = ["fill-160x456|format-webp", "fill-320x912|format-webp"]
STRIP_SMALL = ["fill-101x289|format-webp", "fill-202x578|format-webp", "fill-303x867|format-webp"]

# Raster: ganze Bilder, unbeschnitten
GRID = ["width-480|format-webp", "width-960|format-webp", "width-1440|format-webp"]

# Porträt auf der About-Seite
PORTRAIT = ["fill-320x320|format-webp", "fill-640x640|format-webp"]

BY_LAYOUT = {"grid": GRID, "strip_large": STRIP_LARGE, "strip_small": STRIP_SMALL}


def warm(images, specs):
    """Erzeugt die genannten Größen samt Großansicht für alle Bilder."""
    for image in images:
        image.get_renditions(*specs, *LIGHTBOX)


def with_renditions(queryset):
    """Lädt Bilder und ihre vorhandenen Größen in zwei Abfragen statt in einer pro Bild."""
    return queryset.select_related("image").prefetch_related("image__renditions")
