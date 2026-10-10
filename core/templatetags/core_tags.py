from django import template
from wagtail.models import Site

register = template.Library()


@register.inclusion_tag("includes/main_nav.html", takes_context=True)
def main_nav(context):
    """Hauptnavigation aus dem Seitenbaum.

    Zeigt die Startseite und darunter alle veröffentlichten Seiten, bei denen im
    Admin unter "Werbung" der Haken "In Menüs anzeigen" gesetzt ist. Die
    Reihenfolge entspricht der im Seitenbaum.
    """
    request = context.get("request")
    site = Site.find_for_request(request) if request else None
    if site is None:
        return {"items": []}

    root = site.root_page
    current = context.get("page")
    current_path = getattr(current, "path", "")

    items = [{"page": root, "active": current_path == root.path}]
    for child in root.get_children().live().in_menu():
        # Aktiv ist ein Menüpunkt auch dann, wenn man auf einer seiner Unterseiten ist.
        items.append({"page": child, "active": current_path.startswith(child.path)})
    return {"items": items, "request": request}


@register.filter
def aspect_ratio(image):
    """Breite durch Höhe eines Bildes, als Zahl für CSS (Punkt als Dezimaltrenner)."""
    if not image or not image.height:
        return "1.5"
    return f"{image.width / image.height:.4f}"
