from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def require_current_database():
    """Bricht mit einer verständlichen Meldung ab, wenn Migrationen ausstehen.

    Typischer Fall: Nach "docker compose restart" laufen die Migrationen noch im
    Hintergrund, während schon der nächste Befehl startet.
    """
    executor = MigrationExecutor(connection)
    pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
    if pending:
        names = ", ".join(f"{migration.app_label}.{migration.name}" for migration, _backwards in pending)
        raise CommandError(
            "Die Datenbank ist noch nicht auf dem neuesten Stand (ausstehend: "
            f"{names}). Erst ausführen: docker compose exec web python manage.py migrate"
        )
