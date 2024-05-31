from django.db.migrations import operations
from django.db.migrations.state import ModelState

from django_db_views.context_manager import VIEW_MIGRATION_CONTEXT
from django_db_views.db_view import DBView, DBMaterializedView
from django_db_views.migration_functions import (
    ForwardMaterializedViewMigration,
    ForwardViewMigration,
)


def get_table_engine_name_hash(table_name, engine):
    return f"{table_name}_{engine}".lower()


class DBViewModelState(ModelState):
    def __init__(
        self,
        *args,
        # Not required cus migrate also load state using clone method that do not provide required by us fields.
        view_engine: str = None,
        view_definition: str = None,
        table_name: str = None,
        base_class=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if VIEW_MIGRATION_CONTEXT["is_view_migration"]:
            self.view_engine = view_engine
            self.view_definition = view_definition
            self.base_class = base_class
            self.table_name = table_name


class ViewRunPython(operations.RunPython):
    reduces_to_sql = True

    def state_forwards(self, app_label, state):
        if VIEW_MIGRATION_CONTEXT["is_view_migration"]:
            if isinstance(self.code, ForwardMaterializedViewMigration):
                model = DBMaterializedView
            elif isinstance(self.code, ForwardViewMigration):
                model = DBView
            else:
                raise NotImplementedError
            state.add_model(
                DBViewModelState(
                    app_label,
                    # Hash table_name_engine_name to add state model per migration, which are added per engine.
                    get_table_engine_name_hash(
                        self.code.table_name, self.code.view_engine
                    ),
                    list(),
                    dict(),
                    # we do not use django bases (they initialize model using that, and broke ViewRegistry),
                    # instead of that we pass bass class in separate argument.
                    tuple(),
                    list(),
                    view_engine=self.code.view_engine,
                    view_definition=self.code.view_definition,
                    base_class=model,
                    table_name=self.code.table_name,
                )
            )

    def describe(self):
        return "View migration operation"


class ViewDropRunPython(operations.RunPython):
    def state_forwards(self, app_label, state):
        if VIEW_MIGRATION_CONTEXT["is_view_migration"]:
            state.remove_model(
                app_label,
                get_table_engine_name_hash(self.code.table_name, self.code.view_engine),
            )
