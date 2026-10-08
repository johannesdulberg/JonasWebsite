"""Lädt alle Fotos der bisherigen Wix-Seite in Originalgröße herunter.

Aufruf (Container muss laufen):

    docker compose exec web python scripts/fetch_wix_images.py

Ergebnis: Ordner wix_import/ mit einem Unterordner pro Seite und einer
manifest.json, die Reihenfolge, Alt-Texte und Herkunft festhält. Der Ordner
steht in .gitignore, die Fotos landen also nicht im Repo.

Das Skript kann beliebig oft laufen. Vorhandene Dateien lädt es nicht erneut,
und Seiten, die schon vollständig in der manifest.json stehen, fragt es nicht
noch einmal ab. Mit --neu liest es alle Seiten frisch von Wix, zum Beispiel
wenn dort Bilder dazugekommen sind.

Hintergrund: Wix liefert Bilder verkleinert aus, über Adressen wie
    https://static.wixstatic.com/media/<id>~mv2.jpg/v1/fill/w_160,h_456,.../<name>.jpg
Ohne den Teil ab /v1/ kommt die Datei so, wie sie hochgeladen wurde.
"""

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
        if previous and all((OUT_DIR / item["file"]).exists() for item in previous["items"]):
            manifest["pages"][name] = previous
            print(f"\n== {name}: bereits vollständig, übersprungen", flush=True)
            continue

        if requested:
            time.sleep(PAUSE_BETWEEN_PAGES)
        requested = True
        print(f"\n== {name} ({SITE}{path})", flush=True)
        try:
            html = fetch(SITE + path).decode("utf-8", errors="replace")
        except Exception as error:
            print(f"   Seite nicht abrufbar: {error}")
            errors += 1
            continue

        images, videos = find_media(html)
        page_dir = OUT_DIR / name
        page_dir.mkdir(exist_ok=True)
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

        manifest["pages"][name] = {"path": path, "items": entries}
        print(f"   -> {len(images)} Bilder, {len(videos)} Videos")

    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print("\nZusammenfassung")
    for name, page in manifest["pages"].items():
        kinds = [item["type"] for item in page["items"]]
        print(f"   {name:<12}{kinds.count('image'):>4} Bilder{kinds.count('video'):>4} Videos")
    print(f"   Fehler: {errors}")
    print(f"   Ablage: {OUT_DIR}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
