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

# Tailwind als einzelne ausführbare Datei (Standalone-CLI, braucht kein Node).
# TARGETARCH setzt Docker selbst: arm64 auf Apple-Silicon-Macs, amd64 auf üblichen Servern.
ARG TAILWIND_VERSION=4.3.3
ARG TARGETARCH
RUN if [ "$TARGETARCH" = "arm64" ]; then arch=arm64; else arch=x64; fi \
 && python -c "import sys, urllib.request; urllib.request.urlretrieve(sys.argv[1], '/usr/local/bin/tailwindcss')" \
      "https://github.com/tailwindlabs/tailwindcss/releases/download/v${TAILWIND_VERSION}/tailwindcss-linux-${arch}" \
 && chmod +x /usr/local/bin/tailwindcss

COPY --chown=wagtail:wagtail . .

# CSS für die Produktion erzeugen. In der Entwicklung übernimmt das der tailwind-Container.
RUN tailwindcss -i config/static_src/tailwind.css -o config/static/css/tailwind.css --minify \
 && chown wagtail:wagtail config/static/css/tailwind.css

# Die Ordner müssen im Image existieren und dem Benutzer gehören,
# damit die eingehängten Volumes dieselben Rechte bekommen.
RUN mkdir -p /app/static /app/media && chown wagtail:wagtail /app /app/static /app/media

USER wagtail

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
