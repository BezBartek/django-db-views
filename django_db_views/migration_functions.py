from django.utils.deconstruct import deconstructible


class ViewMigration(object):
    DROP_COMMAND_TEMPLATE: str
    CREATE_COMMAND_TEMPLATE: str

    def __init__(self, view_definition: str, table_name: str, engine=None):
        # if provided engine is None, then we are assuming that engine is same as db engine.
        # We do that to keep backward compatibility.
        self.view_engine = engine
        self.view_definition = view_definition
        self.table_name = table_name


class ForwardViewMigrationBase(ViewMigration):
    def __call__(self, apps, schema_editor):
        if self.view_definition:
            if (
                self.view_engine is None
                or self.view_engine == schema_editor.connection.settings_dict["ENGINE"]
            ):
                schema_editor.execute(self.DROP_COMMAND_TEMPLATE % self.table_name)
                schema_editor.execute(
                    self.CREATE_COMMAND_TEMPLATE
                    % (self.table_name, self.view_definition)
                )


class BackwardViewMigrationBase(ViewMigration):
    def __call__(self, apps, schema_editor):
        if (
            self.view_engine is None
            or self.view_engine == schema_editor.connection.settings_dict["ENGINE"]
        ):
            schema_editor.execute(self.DROP_COMMAND_TEMPLATE % self.table_name)
        if self.view_definition:
            if (
                self.view_engine is None
                or self.view_engine == schema_editor.connection.settings_dict["ENGINE"]
            ):
                schema_editor.execute(
                    self.CREATE_COMMAND_TEMPLATE
                    % (self.table_name, self.view_definition)
                )


@deconstructible
class ForwardViewMigration(ForwardViewMigrationBase):
    DROP_COMMAND_TEMPLATE = "DROP VIEW IF EXISTS %s;"
    CREATE_COMMAND_TEMPLATE = "CREATE VIEW %s as %s;"


@deconstructible
class BackwardViewMigration(BackwardViewMigrationBase):
    DROP_COMMAND_TEMPLATE = "DROP VIEW IF EXISTS %s;"
    CREATE_COMMAND_TEMPLATE = "CREATE VIEW %s as %s;"


@deconstructible
class ForwardMaterializedViewMigration(ForwardViewMigrationBase):
    DROP_COMMAND_TEMPLATE = "DROP MATERIALIZED VIEW IF EXISTS %s;"
    CREATE_COMMAND_TEMPLATE = "CREATE MATERIALIZED VIEW %s as %s;"


@deconstructible
class BackwardMaterializedViewMigration(BackwardViewMigrationBase):
    DROP_COMMAND_TEMPLATE = "DROP MATERIALIZED VIEW IF EXISTS %s;"
    CREATE_COMMAND_TEMPLATE = "CREATE MATERIALIZED VIEW %s as %s;"


class DropViewMigration(object):
    DROP_COMMAND_TEMPLATE: str

    def __init__(self, table_name: str, engine=None):
        self.table_name = table_name
        self.view_engine = engine

    def __call__(self, apps, schema_editor):
        if (
            self.view_engine is None
            or self.view_engine == schema_editor.connection.settings_dict["ENGINE"]
        ):
            schema_editor.execute(self.DROP_COMMAND_TEMPLATE % self.table_name)


@deconstructible
class DropMaterializedView(DropViewMigration):
    DROP_COMMAND_TEMPLATE = "DROP MATERIALIZED VIEW IF EXISTS %s;"


@deconstructible
class DropView(DropViewMigration):
    DROP_COMMAND_TEMPLATE = "DROP VIEW IF EXISTS %s;"
