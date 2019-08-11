from django.utils.deconstruct import deconstructible


class ViewMigration(object):

    def __init__(self, view_definition: str, table_name: str):
        self.view_definition = view_definition
        self.table_name = table_name

    def __call__(self, apps, schema_editor):
        schema_editor.execute(
            'DROP VIEW IF EXISTS %s;' % self.table_name
        )
        if self.view_definition:
            schema_editor.execute(
                """CREATE VIEW %s AS %s;""" % (self.table_name, self.view_definition)
            )


@deconstructible
class ForwardViewMigration(ViewMigration):
    pass


@deconstructible
class BackwardViewMigration(ViewMigration):
    pass
