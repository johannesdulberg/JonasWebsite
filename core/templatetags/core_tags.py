from django import template
from wagtail.models import Site

from core.models import SiteSettings

register = template.Library()


@register.inclusion_tag("includes/main_nav.html", takes_context=True)
def main_nav(context):
    """Hauptnavigation aus dem Seitenbaum.

    Zeigt die Startseite und darunter alle veröffentlichten Seiten, bei denen im
    Admin unter "Werbung" der Haken "In Menüs anzeigen" gesetzt ist. Die
    Reihenfolge entspricht der im Seitenbaum. Die Seite für den Termin-Knopf
    (Einstellungen -> Kopf- und Fußzeile) erscheint nicht in der Liste, sondern
    als Knopf.
    """
    request = context.get("request")
    site = Site.find_for_request(request) if request else None
    if site is None:
        return {"items": []}

    root = site.root_page
    current = context.get("page")
    current_path = getattr(current, "path", "")
    settings = SiteSettings.for_site(site)
    booking = settings.booking_page if settings.booking_page_id and settings.booking_page.live else None

    items = [{"page": root, "active": current_path == root.path}]
    for child in root.get_children().live().in_menu():
        if booking and child.pk == booking.pk:
            continue
        # Aktiv ist ein Menüpunkt auch dann, wenn man auf einer seiner Unterseiten ist.
        items.append({"page": child, "active": current_path.startswith(child.path)})
    return {
        "items": items,
        "booking": booking,
        "booking_active": bool(booking and current_path.startswith(booking.path)),
        "booking_text": settings.booking_button_text,
        "request": request,
    }


@register.simple_tag(takes_context=True)
def booking_cta(context):
    """Die Seite für den Termin-Knopf, wenn er über der Fußzeile erscheinen soll.

    Nicht auf der Seite selbst und nicht auf ihren Unterseiten.
    """
    request = context.get("request")
    if request is None:
        return None
    booking = SiteSettings.for_request(request).booking_page
    if booking is None or not booking.live:
        return None
    current = context.get("page")
    if current is not None and getattr(current, "path", "").startswith(booking.path):
        return None
    return booking


@register.filter
def aspect_ratio(image):
    """Breite durch Höhe eines Bildes, als Zahl für CSS (Punkt als Dezimaltrenner)."""
    if not image or not image.height:
        return "1.5"
    return f"{image.width / image.height:.4f}"


@register.filter
def focal_position(image):
    """CSS object-position aus dem Fokuspunkt, damit beschnittene Kacheln die richtige Stelle zeigen."""
    if not image or image.focal_point_x is None or not image.width or not image.height:
        return "object-position: 50% 50%"
    x = 100 * image.focal_point_x / image.width
    y = 100 * image.focal_point_y / image.height
    return f"object-position: {x:.1f}% {y:.1f}%"
