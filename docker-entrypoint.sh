#!/bin/sh
# Läuft bei jedem Start des Containers, bevor der eigentliche Befehl startet.
set -e

python manage.py migrate --noinput

# In Produktion liefert nginx die statischen Dateien aus dem Volume aus.
# In der Entwicklung macht das der Django-Entwicklungsserver selbst.
case "$DJANGO_SETTINGS_MODULE" in
  *production) python manage.py collectstatic --noinput ;;
esac

exec "$@"
