from django.apps import apps
from django.db import connection

from django_db_views.autodetector import ViewMigrationAutoDetector

try:
    import pytest
except ImportError:
    raise Exception("fixtures are available only for pytest.")


@pytest.fixture(autouse=True, scope="session")
def django_db_views_setup(
    django_db_setup,
    request,
    django_db_blocker,
    django_db_use_migrations: bool,
    django_db_keepdb: bool,
) -> None:
    def no_migrations_tear_up() -> None:
        view_models = ViewMigrationAutoDetector.get_current_view_models()
        with django_db_blocker.unblock(), connection.schema_editor() as schema_editor:
            engine = schema_editor.connection.settings_dict["ENGINE"]
            for view_model in view_models.values():
                view_definition = (
                    ViewMigrationAutoDetector.get_view_definition_from_model(
                        view_model
                    )[engine]
                )
                forward_migration = (
                    ViewMigrationAutoDetector.get_forward_migration_class(view_model)(
                        view_definition.strip(";"),
                        view_model._meta.db_table,
                        engine=engine,
                    )
                )
                # run migration
                forward_migration(apps, schema_editor)

    def no_migrations_teardown() -> None:
        view_models = ViewMigrationAutoDetector.get_current_view_models()
        with django_db_blocker.unblock(), connection.schema_editor() as schema_editor:
            engine = schema_editor.connection.settings_dict["ENGINE"]
            for view_model in view_models.values():
                backward_migration = (
                    ViewMigrationAutoDetector.get_backward_migration_class(view_model)(
                        "",
                        view_model._meta.db_table,
                        engine=engine,
                    )
                )
                # run migration
                backward_migration(apps, schema_editor)

    if not django_db_use_migrations:
        no_migrations_tear_up()

    if not django_db_keepdb:
        request.addfinalizer(no_migrations_teardown)
