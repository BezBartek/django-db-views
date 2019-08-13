from django.utils.deconstruct import deconstructible


class ViewMigration(object):

    def __init__(self, view_definition: str, table_name: str):
        self.view_definition = view_definition
        self.table_name = table_name


@deconstructible
class ForwardViewMigration(ViewMigration):

    def __call__(self, apps, schema_editor):
        if self.view_definition:
            schema_editor.execute(
                """CREATE OR REPLACE VIEW %s AS %s;""" % (self.table_name, self.view_definition)
            )


@deconstructible
class BackwardViewMigration(ViewMigration):

    def __call__(self, apps, schema_editor):
        if self.view_definition:
            schema_editor.execute(
                """CREATE OR REPLACE VIEW %s AS %s;""" % (self.table_name, self.view_definition)
            )
        else:
            schema_editor.execute(
                'DROP VIEW IF EXISTS %s;' % self.table_name
            )
