import re
from itertools import zip_longest

import six
from django.apps import apps
from django.db import connection, ProgrammingError
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.graph import MigrationGraph

from django_db_views.db_view import DBView
from django_db_views.operations import ViewRunPython
from django_db_views.migration_functions import ForwardViewMigration, BackwardViewMigration


class ViewMigrationAutoDetector(MigrationAutodetector):

    def _detect_changes(self, convert_apps=None, graph=None)->dict:
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

        # Renames have to come first
        self.generate_views_operations(graph)

        self._sort_migrations()
        self._build_migration_list(graph)
        self._optimize_migrations()

        return self.migrations

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

    def generate_views_operations(self, graph: MigrationGraph)->None:   # it's correct? or Type[None]
        view_models = self.get_view_models()

        for (app_label, model_name), view_model in view_models.items():

            current_view_definition = self.get_previous_view_definition_state(
                graph, app_label, view_model._meta.db_table
            )

            new_view_definition = view_model.view_definition.strip()
            if not self.is_same_views(current_view_definition, new_view_definition):
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
                        ForwardViewMigration(new_view_definition, view_model._meta.db_table),
                        BackwardViewMigration(current_view_definition, view_model._meta.db_table)
                    ),
                    dependencies=dependencies,
                )

    def get_previous_view_definition_state(self, graph: MigrationGraph, app_label: str, for_table_name: str):
        last_node = graph.leaf_nodes(app_label)[0]

        while last_node:
            migration = graph.nodes[last_node]
            if migration.operations:
                if len(migration.operations) == 1:
                    if isinstance(migration.operations[0], ViewRunPython):
                        table_name = migration.operations[0].code.table_name
                        previous_view_definition = migration.operations[0].code.view_definition
                        if table_name == for_table_name:
                            return previous_view_definition.strip()
            # right now i get only migrations from the same app.
            app_parents = list(sorted(filter(lambda x: x[0] == app_label, graph.node_map[last_node].parents)))
            if app_parents:
                last_node = app_parents[-1]
            else:   # if no parents mean we found initial migration
                last_node = None
        return None

    def get_current_view_definition_from_database(self, table_name: str)->str:
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT pg_get_viewdef('%s')" % table_name)
                current_view_definition = cursor.fetchone()[0].strip()
            except ProgrammingError:  # VIEW NOT EXIST
                current_view_definition = ""
            finally:
                return current_view_definition
