FROM python:3.13-slim-bookworm

# Ausgaben sofort ins Log schreiben, keine .pyc-Dateien anlegen.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Die Anwendung läuft nicht als root.
RUN useradd --create-home wagtail

WORKDIR /app

# Abhängigkeiten zuerst: Dieser Schritt wird nur neu gebaut, wenn sich requirements.txt ändert.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=wagtail:wagtail . .

# Die Ordner müssen im Image existieren und dem Benutzer gehören,
# damit die eingehängten Volumes dieselben Rechte bekommen.
RUN mkdir -p /app/static /app/media && chown wagtail:wagtail /app /app/static /app/media

USER wagtail

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
