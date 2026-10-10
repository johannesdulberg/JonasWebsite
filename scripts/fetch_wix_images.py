"""Lädt Fotos, Videos und Texte der bisherigen Wix-Seite herunter.

Aufruf (Container muss laufen):

    docker compose exec web python scripts/fetch_wix_images.py

Ergebnis: Ordner wix_import/ mit einem Unterordner pro Seite und einer
manifest.json. Die hält pro Seite fest:

  items    alle Bilder und Videos mit Datei und Reihenfolge
  content  den Inhalt in der Reihenfolge des Seitenquelltexts: Überschriften,
           Absätze, Bilder (mit Kachelgröße und Fokuspunkt), Formularfelder

Der Ordner steht in .gitignore, die Fotos landen also nicht im Repo.

Das Skript kann beliebig oft laufen. Vorhandene Dateien lädt es nicht erneut,
und den Quelltext jeder Seite legt es als page.html ab, damit es Wix dafür
nur einmal fragen muss. Mit --neu liest es alle Seiten frisch von Wix, zum
Beispiel wenn dort etwas geändert wurde.

Hintergrund: Wix liefert Bilder verkleinert aus, über Adressen wie
    https://static.wixstatic.com/media/<id>~mv2.jpg/v1/fill/w_160,h_456,.../<name>.jpg
Ohne den Teil ab /v1/ kommt die Datei so, wie sie hochgeladen wurde.
"""

import html as html_module
import json
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

SITE = "https://www.jonasduelberg.com"
# Schlüssel = Ordnername, Wert = Pfad auf der Wix-Seite
PAGES = {
    "home": "/",
    "commercial": "/commercial",
    "outdoor": "/outdoor",
    "other": "/other",
    "booking": "/booking",
    "about": "/about",
    "impressum": "/impressum",
}
# Alle eigenen Uploads beginnen mit dieser Kennung des Wix-Kontos.
# Das schließt fremde Dateien wie die Social-Media-Icons aus.
OWNER = "c5ec14"

OUT_DIR = Path(__file__).resolve().parent.parent / "wix_import"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

IMAGE_RE = re.compile(rf"({OWNER}_[0-9a-f]{{32}}~mv2\.(?:jpe?g|png|webp|gif))", re.I)
VIDEO_RE = re.compile(rf"({OWNER}_[0-9a-f]{{32}})/(\d+)p/mp4/file\.mp4", re.I)


# Wix bremst zu viele Anfragen in kurzer Zeit mit "429 Too Many Requests" aus.
# Deshalb Pausen zwischen den Anfragen und geduldiges Warten, wenn es doch passiert.
PAUSE_BETWEEN_DOWNLOADS = 1.5  # Sekunden
PAUSE_BETWEEN_PAGES = 10
WAIT_ON_429 = [30, 60, 120, 240]  # Wartezeiten vor dem 2., 3., ... Versuch


def fetch(url):
    """Holt eine Adresse und gibt die Bytes zurück."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    attempts = len(WAIT_ON_429) + 1
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if attempt == attempts:
                raise
            if error.code == 429:
                # Nennt Wix selbst eine Wartezeit, gilt die.
                announced = error.headers.get("Retry-After", "") if error.headers else ""
                wait = int(announced) if announced.isdigit() else WAIT_ON_429[attempt - 1]
                print(f"   Wix bremst (429), warte {wait} s ...", flush=True)
            elif 400 <= error.code < 500:
                raise  # z. B. 404 ändert sich durch Wiederholen nicht
            else:
                wait = 5 * attempt
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts:
                raise
            wait = 5 * attempt
        time.sleep(wait)


class ImgCollector(HTMLParser):
    """Sammelt die <img>-Tags in der Reihenfolge, in der sie auf der Seite stehen."""

    def __init__(self):
        super().__init__()
        self.images = []  # Liste aus (Datei-ID, Alt-Text)

    def handle_starttag(self, tag, attrs):
        if tag != "img":
            return
        attrs = dict(attrs)
        source = " ".join(filter(None, [attrs.get("src"), attrs.get("data-src"), attrs.get("srcset")]))
        match = IMAGE_RE.search(source)
        if match:
            self.images.append((match.group(1), (attrs.get("alt") or "").strip()))


TILE_RE = re.compile(r"/v1/[a-z]+/w_(\d+),h_(\d+)(?:[^/]*?fp_([\d.]+)_([\d.]+))?")
TEXT_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "label", "button"}
IGNORED_TAGS = {"script", "style", "noscript", "svg", "header", "footer", "nav"}
FIELD_TAGS = {"input", "textarea", "select"}


class ContentCollector(HTMLParser):
    """Liest den Inhalt einer Seite in der Reihenfolge des Quelltexts.

    Ergebnis ist eine Liste aus Einträgen:
      {"type": "text", "tag": "h2" | "p" | ..., "text": "...", "html": "..."}
      {"type": "image", "id": "...", "alt": "...", "width": 160, "height": 456, "focal_point": [0.5, 0.3]}
      {"type": "field", "kind": "input" | "textarea", "name": "...", "label": "..."}

    Berücksichtigt wird nur, was in <main> steht (ohne Kopf- und Fußzeile). In
    "html" bleiben Links und Zeilenumbrüche erhalten, alles andere ist Text.
    """

    def __init__(self, only_main):
        super().__init__(convert_charrefs=True)
        self.only_main = only_main
        self.main_depth = 0
        self.ignored = []  # Stapel der gerade offenen Tags, deren Inhalt nicht zählt
        self.block = None  # Tag des Textblocks, der gerade gesammelt wird
        self.text = []
        self.markup = []
        self.items = []

    def active(self):
        return not self.ignored and (self.main_depth > 0 or not self.only_main)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "main":
            self.main_depth += 1
        if tag in IGNORED_TAGS:
            self.ignored.append(tag)
            return
        if not self.active():
            return

        if tag == "img":
            source = " ".join(filter(None, [attrs.get("src"), attrs.get("data-src"), attrs.get("srcset")]))
            match = IMAGE_RE.search(source)
            if match:
                entry = {"type": "image", "id": match.group(1), "alt": (attrs.get("alt") or "").strip()}
                tile = TILE_RE.search(source)
                if tile:
                    entry["width"], entry["height"] = int(tile.group(1)), int(tile.group(2))
                    if tile.group(3):
                        entry["focal_point"] = [float(tile.group(3)), float(tile.group(4))]
                self.items.append(entry)
        elif tag == "video":
            self.items.append({"type": "video", "src": attrs.get("src") or "", "poster": attrs.get("poster") or ""})
        elif tag in FIELD_TAGS and attrs.get("type") not in {"hidden", "submit"}:
            self.items.append(
                {
                    "type": "field",
                    "kind": tag,
                    "input_type": attrs.get("type") or "",
                    "name": attrs.get("name") or "",
                    "label": attrs.get("aria-label") or attrs.get("placeholder") or "",
                    "required": "required" in attrs,
                }
            )
        elif tag in TEXT_TAGS:
            # Ein Absatz in einem Listenpunkt (<li><p>) zählt als der Listenpunkt selbst.
            if self.block is None:
                self.block, self.text, self.markup = tag, [], []
        elif self.block:
            if tag == "br":
                self.text.append("\n")
                self.markup.append("<br/>")
            elif tag == "a" and attrs.get("href"):
                self.markup.append(f'<a href="{html_module.escape(attrs["href"], quote=True)}">')

    def handle_endtag(self, tag):
        if tag == "main":
            self.main_depth = max(0, self.main_depth - 1)
        if self.ignored and tag == self.ignored[-1]:
            self.ignored.pop()
            return
        if not self.block:
            return
        if tag == "a":
            self.markup.append("</a>")
        elif tag == self.block:
            # Wix füllt leere Zeilen mit unsichtbaren Zeichen, die fliegen raus.
            invisible = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff\xa0"), " ")
            text = " ".join("".join(self.text).translate(invisible).split())
            if text:
                markup = re.sub(r"[ \t\r\n]+", " ", "".join(self.markup).translate(invisible)).strip()
                self.items.append({"type": "text", "tag": tag, "text": text, "html": markup})
            self.block = None

    def handle_data(self, data):
        if self.block and self.active():
            self.text.append(data)
            self.markup.append(html_module.escape(data, quote=False))


def find_content(html):
    """Inhalt einer Seite in Quelltext-Reihenfolge, siehe ContentCollector."""
    collector = ContentCollector(only_main="<main" in html)
    collector.feed(html)
    collector.close()
    return collector.items


def find_media(html):
    """Gibt (Bilder, Videos) einer Seite zurück, jeweils ohne Doppelte."""
    collector = ImgCollector()
    collector.feed(html)

    images = {}  # Datei-ID -> Eintrag; dict behält die Reihenfolge
    for file_id, alt in collector.images:
        entry = images.setdefault(file_id, {"id": file_id, "alt": "", "source": "img"})
        entry["alt"] = entry["alt"] or alt

    # Wix legt Galerie-Daten zusätzlich als JSON in die Seite. Bilder, die erst
    # beim Scrollen als <img> erscheinen, stehen dort schon drin.
    for file_id in IMAGE_RE.findall(html):
        images.setdefault(file_id, {"id": file_id, "alt": "", "source": "data"})

    videos = {}  # Video-ID -> höchste gefundene Auflösung
    for video_id, height in VIDEO_RE.findall(html):
        videos[video_id] = max(videos.get(video_id, 0), int(height))

    return list(images.values()), videos


def download(url, target):
    """Lädt url nach target. Gibt 'neu', 'vorhanden' oder eine Fehlermeldung zurück."""
    if target.exists() and target.stat().st_size > 0:
        return "vorhanden"
    try:
        data = fetch(url)
    except Exception as error:  # ein kaputtes Bild soll den Rest nicht aufhalten
        return f"FEHLER {error}"
    time.sleep(PAUSE_BETWEEN_DOWNLOADS)
    partial = target.with_name(target.name + ".part")
    partial.write_bytes(data)
    partial.rename(target)
    return "neu"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    manifest_file = OUT_DIR / "manifest.json"
    force = "--neu" in sys.argv

    # Ergebnis früherer Läufe. Seiten, die dort schon vollständig stehen, werden
    # nicht noch einmal bei Wix abgefragt (außer mit --neu).
    known = {}
    if manifest_file.exists() and not force:
        known = json.loads(manifest_file.read_text()).get("pages", {})

    manifest = {"site": SITE, "pages": {}}
    errors = 0
    requested = False

    for name, path in PAGES.items():
        previous = known.get(name)
        # "content" kam später dazu: Fehlt es, wird die Seite noch einmal ausgewertet.
        if (
            previous
            and "content" in previous
            and all((OUT_DIR / item["file"]).exists() for item in previous["items"])
        ):
            manifest["pages"][name] = previous
            print(f"\n== {name}: bereits vollständig, übersprungen", flush=True)
            continue

        page_dir = OUT_DIR / name
        page_dir.mkdir(exist_ok=True)
        html_file = page_dir / "page.html"

        if html_file.exists() and not force:
            print(f"\n== {name} (aus gespeichertem Quelltext)", flush=True)
            html = html_file.read_text(encoding="utf-8")
        else:
            if requested:
                time.sleep(PAUSE_BETWEEN_PAGES)
            requested = True
            print(f"\n== {name} ({SITE}{path})", flush=True)
            try:
                html = fetch(SITE + path).decode("utf-8", errors="replace")
            except Exception as error:
                print(f"   Seite nicht abrufbar: {error}")
                errors += 1
                # Was aus einem früheren Lauf bekannt ist, bleibt im Manifest stehen.
                if previous:
                    manifest["pages"][name] = previous
                continue
            html_file.write_text(html, encoding="utf-8")

        images, videos = find_media(html)
        entries = []

        for position, image in enumerate(images, start=1):
            extension = image["id"].rsplit(".", 1)[1].lower()
            filename = f"{position:03d}_{image['id'].split('~')[0]}.{extension}"
            url = f"https://static.wixstatic.com/media/{image['id']}"
            status = download(url, page_dir / filename)
            errors += status.startswith("FEHLER")
            print(f"   {filename}  {status}")
            entries.append(
                {
                    "position": position,
                    "file": f"{name}/{filename}",
                    "type": "image",
                    "url": url,
                    # Wix setzt als Alt-Text oft nur den alten Dateinamen, z. B. DSC09890.jpg
                    "alt": image["alt"],
                    # "img" = stand sichtbar im HTML, "data" = nur in den Galerie-Daten
                    "found_in": image["source"],
                }
            )

        for position, (video_id, height) in enumerate(videos.items(), start=1):
            filename = f"video_{position:02d}_{video_id}.mp4"
            url = f"https://video.wixstatic.com/video/{video_id}/{height}p/mp4/file.mp4"
            status = download(url, page_dir / filename)
            errors += status.startswith("FEHLER")
            print(f"   {filename}  {status}")
            entries.append({"position": position, "file": f"{name}/{filename}", "type": "video", "url": url})

        content = find_content(html)
        texts = sum(item["type"] == "text" for item in content)
        manifest["pages"][name] = {"path": path, "items": entries, "content": content}
        print(f"   -> {len(images)} Bilder, {len(videos)} Videos, {texts} Textblöcke")

    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print("\nZusammenfassung")
    for name, page in manifest["pages"].items():
        kinds = [item["type"] for item in page["items"]]
        texts = sum(item["type"] == "text" for item in page.get("content", []))
        print(
            f"   {name:<12}{kinds.count('image'):>4} Bilder{kinds.count('video'):>4} Videos"
            f"{texts:>5} Textblöcke"
        )
    print(f"   Fehler: {errors}")
    print(f"   Ablage: {OUT_DIR}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
