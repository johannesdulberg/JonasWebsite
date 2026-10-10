# jonaswebsite

Webseite von Jonas Dülberg: Wagtail (Django), Postgres, gunicorn und nginx in Docker.

## Erster Start

```
cp .env.example .env
docker compose up --build
```

In einem zweiten Terminal den Admin-Benutzer anlegen:

```
docker compose exec web python manage.py createsuperuser
```

Seiten, Kopf- und Fußzeile nach Vorbild der bisherigen Seite anlegen (einmalig, überschreibt nichts):

```
docker compose exec web python manage.py seed_site
```

Fotos, Videos und Texte der bisherigen Seite laden und in die Seiten übernehmen:

```
docker compose exec web python scripts/fetch_wix_images.py
docker compose exec web python manage.py import_wix
```

`import_wix` lässt Seiten mit Inhalt unverändert. Einzelne Seiten neu befüllen: `import_wix --seite other --neu`.

- Seite: http://localhost:8000
- Wagtail-Admin: http://localhost:8000/admin/

Das ist die Entwicklungsvariante: Der Code-Ordner ist in den Container eingehängt, Änderungen wirken sofort. Migrationen laufen bei jedem Start automatisch.

Das CSS kommt von Tailwind. Der Container `tailwind` beobachtet die Templates und schreibt bei jeder Änderung `config/static/css/tailwind.css` neu. Eigene CSS-Regeln und Tailwind-Einstellungen gehören in `config/static_src/tailwind.css`.

## Inhalte pflegen

- **Navigation:** entsteht aus dem Seitenbaum. Eine Seite erscheint im Menü, wenn sie direkt unter der Startseite liegt, veröffentlicht ist und im Reiter "Werbung" der Haken "In Menüs anzeigen" gesetzt ist. Die Reihenfolge ist die im Seitenbaum.
- **Startseite:** unter Seiten → Home bearbeiten. Zwei Bereiche (obere und untere Galerie); dort lassen sich mehrere Bilder auf einmal auswählen und per Ziehen sortieren.
- **Galerie-Seiten** (Commercial, Outdoor, Other): bestehen aus Abschnitten. Jeder Abschnitt hat optional Überschrift und Text, eine Darstellung (Raster oder Bildreihe zum Blättern) sowie Bilder und Videos. Neue Galerie-Seite: unter Home "Untergeordnete Seite hinzufügen" → Galerie-Seite.
- **Bildausschnitt:** Bildreihen zeigen Hochformat-Ausschnitte. Welcher Teil eines Fotos sichtbar bleibt, bestimmt der Fokuspunkt (Bilder → Bild anklicken → Fokuspunkt aufziehen). Im Raster und in der Großansicht erscheint immer das ganze Bild.
- **Videos (Cinemagramme):** als MP4 unter Dokumente hochladen und im Abschnitt auswählen. Sie laufen ohne Ton in Schleife.
- **About, Booking, Impressum:** Texte direkt auf der jeweiligen Seite. E-Mail und Telefon auf der Booking-Seite kommen aus den Einstellungen.
- **Kopf- und Fußzeile:** im Admin unter Einstellungen → Kopf- und Fußzeile (Name, Untertitel, Kontakt, Social Media, Impressum-Link, Download). Bei Social-Media-Links eine Plattform wählen, dann erscheint das Icon; ohne Plattform wird es ein Textlink.

Wo der Nachbau bewusst von der Wix-Seite abweicht, steht in [ABWEICHUNGEN.md](ABWEICHUNGEN.md). Offene Aufgaben und Vorschläge stehen in [TODO.md](TODO.md).

## Tests

```
docker compose exec web python manage.py test
```

## Wie auf dem Server (mit nginx und gunicorn)

```
docker compose down
docker compose -f compose.yaml up --build
```

Seite: http://localhost:8080

Vorher `docker compose down`, weil beide Varianten dieselben Containernamen benutzen. Die Daten bleiben erhalten.

## Häufige Befehle

| Zweck | Befehl |
| --- | --- |
| Stoppen | `docker compose down` |
| Logs ansehen | `docker compose logs -f web` |
| Migrationen erzeugen | `docker compose exec web python manage.py makemigrations` |
| Django-Shell | `docker compose exec web python manage.py shell` |
| Alles löschen, auch Datenbank und Fotos | `docker compose down -v` |

## Aufbau

| Pfad | Inhalt |
| --- | --- |
| `config/settings/` | `base.py` gilt immer, `dev.py` für die Entwicklung, `production.py` für den Server |
| `core/` | Einstellungen für Kopf- und Fußzeile, Navigation |
| `home/` | Startseite mit den beiden Galerien |
| `pages/` | Galerie-, About-, Booking- und Textseite, Import der Wix-Inhalte |
| `search/` | Suche aus der Wagtail-Vorlage |
| `Dockerfile`, `docker-entrypoint.sh` | Image der Anwendung und Startskript (Migrationen, statische Dateien) |
| `compose.yaml` | Die drei Container wie auf dem Server |
| `compose.override.yaml` | Abweichungen für die Entwicklung, wird automatisch dazugeladen |
| `config/static_src/tailwind.css` | Eingabedatei für Tailwind |
| `nginx/default.conf` | nginx-Konfiguration |
| `.env` | Geheimnisse und Einstellungen pro Umgebung, nicht im Repo (Vorlage: `.env.example`) |

Datenbank und hochgeladene Fotos liegen in den Docker-Volumes `db_data` und `media_files`.
