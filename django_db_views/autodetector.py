import re
from itertools import zip_longest

import six
from django.apps import apps
from django.conf import settings
from django.db import connection, ProgrammingError
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.graph import MigrationGraph

from django_db_views.db_view import DBView
from django_db_views.operations import ViewRunPython
from django_db_views.migration_functions import ForwardViewMigration, BackwardViewMigration


class ViewMigrationAutoDetector(MigrationAutodetector):
    """
        We overwritten only _detect_changes function.
        It's almost same code as in regular function,
        we just removed generating other operations, and instead of them added our detection.
        rest methods are fully our code which we use for detection.
        It's detect only view model changes.
    """
    def _detect_changes(self, convert_apps=None, graph=None)->dict:

        # <START copy paste from MigrationAutodetector>

        self.generated_operations = {}
        self.altered_indexes = {}

        # Prepare some old/new state and model lists, separating
        # proxy models and ignoring unmigrated apps.
        self.old_apps = self.from_state.concrete_apps
        self.new_apps = self.to_state.apps
        self.old_model_keys = []
        self.old_proxy_keys = []
        self.old_unmanaged_keys = []
        self.new_model_keys = []
        self.new_proxy_keys = []
        self.new_unmanaged_keys = []

        for al, mn in sorted(self.from_state.models.keys()):
            model = self.old_apps.get_model(al, mn)
            if not model._meta.managed:
                self.old_unmanaged_keys.append((al, mn))
            elif al not in self.from_state.real_apps:
                if model._meta.proxy:
                    self.old_proxy_keys.append((al, mn))
                else:
                    self.old_model_keys.append((al, mn))

        for al, mn in sorted(self.to_state.models.keys()):
            model = self.new_apps.get_model(al, mn)
            if not model._meta.managed:
                self.new_unmanaged_keys.append((al, mn))
            elif (
                    al not in self.from_state.real_apps or
                    (convert_apps and al in convert_apps)
            ):
                if model._meta.proxy:
                    self.new_proxy_keys.append((al, mn))
                else:
                    self.new_model_keys.append((al, mn))

        # <END of copy paste from MigrationAutodetector>

        self.generate_views_operations(graph)

        # <START copy paste from MigrationAutodetector>
        self._sort_migrations()
        self._build_migration_list(graph)
        self._optimize_migrations()

        return self.migrations
        # <END end of copy paste from MigrationAutodetector>

    def get_view_models(self)->dict:
        view_models = {}
        for app_label, models in apps.all_models.items():
            for model_name, model_class in models.items():
                if issubclass(model_class, DBView):
                    key = (app_label, model_name)
                    view_models[key] = model_class
        return view_models

    def is_same_views(self, current: str, new: str)->bool:
        if not current:
            return False
        s1_words = filter(lambda x: len(x) != 0, re.split(pattern="[^a-zA-Z]*", string=current))
        s2_words = filter(lambda x: len(x) != 0, re.split(pattern="[^a-zA-Z]*", string=new))
        for w1, w2 in zip_longest(s1_words, s2_words):
            if not w1 or not w2:
                return False
            if w1.lower() != w2.lower():
                return False
        return True

    def generate_views_operations(self, graph: MigrationGraph) -> None:
        view_models = self.get_view_models()
        for (app_label, model_name), view_model in view_models.items():
            new_view_definition = self.get_view_definition_from_model(view_model)
            for engine, latest_view_definition in new_view_definition.items():
                current_view_definition = self.get_previous_view_definition_state(
                    graph, app_label, view_model._meta.db_table, engine
                )
                if not self.is_same_views(current_view_definition, latest_view_definition):
                    # Depend on all bases
                    model_state = self.to_state.models[app_label, model_name]
                    dependencies = []
                    for base in model_state.bases:
                        if isinstance(base, six.string_types) and "." in base:
                            base_app_label, base_name = base.split(".", 1)
                            dependencies.append((base_app_label, base_name, None, True))
                    self.add_operation(
                        app_label,
                        ViewRunPython(
                            ForwardViewMigration(latest_view_definition.strip(";"),
                                                 view_model._meta.db_table, engine=engine),
                            BackwardViewMigration(current_view_definition.strip(";"),
                                                  view_model._meta.db_table, engine=engine),
                            atomic=False
                        ),
                        dependencies=dependencies,
                    )

    def get_view_definition_from_model(self, view_model: DBView) -> dict:
        view_definition = {}

        if isinstance(view_model.view_definition, dict):
            for engine, definition in view_model.view_definition.items():
                view_definition[engine] = self.get_cleaned_view_definition_value(definition)
                assert isinstance(view_definition[engine], str), \
                    "View definition must be callable and return string or be itself a string."
        else:
            engine = settings.DATABASES['default']['ENGINE']
            view_definition[engine] = self.get_cleaned_view_definition_value(view_model.view_definition)
            assert isinstance(view_definition[engine], str), \
                "View definition must be callable and return string or be itself a string."
        return view_definition

    def get_previous_view_definition_state(self, graph: MigrationGraph, app_label: str, for_table_name: str, engine: str):
        nodes = graph.leaf_nodes(app_label)
        last_node = nodes[0] if nodes else None

        while last_node:
            migration = graph.nodes[last_node]
            if migration.operations:
                for operation in migration.operations:
                    if isinstance(operation, ViewRunPython):
                        table_name = operation.code.table_name
                        previous_view_definition = operation.code.view_definition
                        previous_view_engine = operation.code.view_engine \
                            if hasattr(operation.code, 'view_engine') and operation.code.view_engine \
                            else settings.DATABASES['default']['ENGINE']
                        if table_name == for_table_name and previous_view_engine == engine:
                            return previous_view_definition.strip()
            # right now i get only migrations from the same app.
            app_parents = list(sorted(filter(lambda x: x[0] == app_label, graph.node_map[last_node].parents)))
            if app_parents:
                last_node = app_parents[-1]
            else:   # if no parents mean we found initial migration
                last_node = None
        return ""

    def get_cleaned_view_definition_value(self, view_definition):
        if callable(view_definition):
            return view_definition().strip()
        else:
            return view_definition.strip()

    def get_current_view_definition_from_database(self, table_name: str)->str:
        """working only with postgres"""
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT pg_get_viewdef('%s')" % table_name)
                current_view_definition = cursor.fetchone()[0].strip()
            except ProgrammingError:  # VIEW NOT EXIST
                current_view_definition = ""
            finally:
                return current_view_definition
