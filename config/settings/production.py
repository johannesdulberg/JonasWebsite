import os

from .base import *

DEBUG = False


def env_list(name):
    """Kommagetrennte Umgebungsvariable als Liste, leere Einträge fallen weg."""
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


# Ohne gesetzten Schlüssel startet die Anwendung absichtlich nicht.
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# nginx nimmt die Anfrage an und reicht sie per HTTP weiter. Über diesen Header
# erfährt Django, ob der Besucher per HTTPS kam.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Erst einschalten, wenn auf dem Server ein Zertifikat eingerichtet ist.
if os.environ.get("DJANGO_SECURE_SSL", "false").lower() == "true":
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"][
    "BACKEND"
] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

try:
    from .local import *
except ImportError:
    pass
