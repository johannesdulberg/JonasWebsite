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

Fotos, Videos und Texte der bisherigen Seite aus dem Ordner `wix_import/` in die Seiten übernehmen (der Ordner liegt nur lokal und ist nicht im Repo):

```
docker compose exec web python manage.py import_wix
```

`import_wix` lässt Seiten mit Inhalt unverändert. Einzelne Seiten neu befüllen: `import_wix --seite foto --neu`.

- Seite: http://localhost:8000
- Wagtail-Admin: http://localhost:8000/admin/

Das ist die Entwicklungsvariante: Der Code-Ordner ist in den Container eingehängt, Änderungen wirken sofort. Migrationen laufen bei jedem Start automatisch.

Das CSS kommt von Tailwind. Der Container `tailwind` beobachtet die Templates und schreibt bei jeder Änderung `config/static/css/tailwind.css` neu. Eigene CSS-Regeln und Tailwind-Einstellungen gehören in `config/static_src/tailwind.css`.

## Inhalte pflegen

- **Navigation:** entsteht aus dem Seitenbaum. Eine Seite erscheint im Menü, wenn sie direkt unter der Startseite liegt, veröffentlicht ist und im Reiter "Werbung" der Haken "In Menüs anzeigen" gesetzt ist. Die Reihenfolge ist die im Seitenbaum.
- **Startseite:** unter Seiten → Home bearbeiten. Zwei Bereiche (obere und untere Galerie); dort lassen sich mehrere Bilder auf einmal auswählen und per Ziehen sortieren.
- **Foto-Bibliothek** (Seite "Foto"): alle Fotos auf einer Seite, oben Filter. Ein Foto erscheint unter einem Filter, wenn es den passenden Tag trägt; Tags setzt man am Bild (Bilder → Bild anklicken → Tags). Welche Tags als Filter erscheinen und in welcher Reihenfolge, steht auf der Seite unter "Filter". Fotos auf die Seite bringen: unter "Fotos" mehrere auf einmal auswählen und per Ziehen sortieren. Am Desktop entsteht daraus eine Collage, auf dem Handy zwei Spalten.
- **Bildausschnitt:** Die Collage und die Bildreihen beschneiden Fotos. Welcher Teil sichtbar bleibt, bestimmt der Fokuspunkt (Bilder → Bild anklicken → Fokuspunkt aufziehen). In der Großansicht erscheint immer das ganze Bild.
- **Video und Social:** vorerst einfache Textseiten, bis feststeht, was dort hinkommt.
- **About, Impressum:** Texte direkt auf der jeweiligen Seite.
- **Booking:** Die Texte stehen vorerst im Template und sind noch nicht im Admin pflegbar (siehe TODO.md). Die E-Mail-Adresse kommt aus den Einstellungen.
- **Kopf- und Fußzeile:** im Admin unter Einstellungen → Kopf- und Fußzeile (Name, Untertitel, Termin-Knopf, Kontakt, Social Media, Impressum-Link, Download). Der Termin-Knopf führt zur dort gewählten Seite; er steht rechts im Menü und über der Fußzeile, die Seite selbst nicht mehr als normaler Menüpunkt. Bei Social-Media-Links eine Plattform wählen, dann erscheint das Icon; ohne Plattform wird es ein Textlink.

Offene Aufgaben und Vorschläge stehen in [TODO.md](TODO.md). Die Wünsche von Jonas stehen getrennt davon in [WUENSCHE.md](WUENSCHE.md).

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
| Migrationen anwenden (nach `git pull`) | `docker compose exec web python manage.py migrate` |
| Django-Shell | `docker compose exec web python manage.py shell` |
| Alles löschen, auch Datenbank und Fotos | `docker compose down -v` |

## Aufbau

| Pfad | Inhalt |
| --- | --- |
| `config/settings/` | `base.py` gilt immer, `dev.py` für die Entwicklung, `production.py` für den Server |
| `core/` | Einstellungen für Kopf- und Fußzeile, Navigation |
| `home/` | Startseite mit den beiden Galerien |
| `pages/` | Foto-Bibliothek, About-, Booking- und Textseite, Import der Wix-Inhalte |
| `search/` | Suche aus der Wagtail-Vorlage |
| `Dockerfile`, `docker-entrypoint.sh` | Image der Anwendung und Startskript (Migrationen, statische Dateien) |
| `compose.yaml` | Die drei Container wie auf dem Server |
| `compose.override.yaml` | Abweichungen für die Entwicklung, wird automatisch dazugeladen |
| `config/static_src/tailwind.css` | Eingabedatei für Tailwind |
| `nginx/default.conf` | nginx-Konfiguration |
| `.env` | Geheimnisse und Einstellungen pro Umgebung, nicht im Repo (Vorlage: `.env.example`) |

Datenbank und hochgeladene Fotos liegen in den Docker-Volumes `db_data` und `media_files`.
