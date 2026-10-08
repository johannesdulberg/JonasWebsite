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

- Seite: http://localhost:8000
- Wagtail-Admin: http://localhost:8000/admin/

Das ist die Entwicklungsvariante: Der Code-Ordner ist in den Container eingehängt, Änderungen wirken sofort. Migrationen laufen bei jedem Start automatisch.

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
| `home/`, `search/` | Apps aus der Wagtail-Vorlage |
| `Dockerfile`, `docker-entrypoint.sh` | Image der Anwendung und Startskript (Migrationen, statische Dateien) |
| `compose.yaml` | Die drei Container wie auf dem Server |
| `compose.override.yaml` | Abweichungen für die Entwicklung, wird automatisch dazugeladen |
| `nginx/default.conf` | nginx-Konfiguration |
| `.env` | Geheimnisse und Einstellungen pro Umgebung, nicht im Repo (Vorlage: `.env.example`) |

Datenbank und hochgeladene Fotos liegen in den Docker-Volumes `db_data` und `media_files`.
