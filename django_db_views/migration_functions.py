from django.conf import settings
from django.utils.deconstruct import deconstructible


class ViewMigration(object):

    def __init__(self, view_definition: str, table_name: str, engine=None):
        self.db_engine = settings.DATABASES['default']['ENGINE']
        # if provided engine is None, then we assuming that engine is same as db engine.
        # We do that to keep backward compatibility.
        self.view_engine = engine or self.db_engine
        self.view_definition = view_definition
        self.table_name = table_name


@deconstructible
class ForwardViewMigration(ViewMigration):

    def __call__(self, apps, schema_editor):
        if self.view_definition and self.db_engine == self.view_engine:
            schema_editor.execute("DROP VIEW IF EXISTS %s;" % self.table_name)
            schema_editor.execute("CREATE VIEW %s as %s;" % (self.table_name, self.view_definition))


@deconstructible
class BackwardViewMigration(ViewMigration):

    def __call__(self, apps, schema_editor):
        if self.db_engine == self.view_engine:
            schema_editor.execute("DROP VIEW IF EXISTS %s;" % self.table_name)
        if self.view_definition and self.db_engine == self.view_engine:
            schema_editor.execute("CREATE VIEW %s as %s;" % (self.table_name, self.view_definition))
