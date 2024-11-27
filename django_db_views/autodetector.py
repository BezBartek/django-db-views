import re
from itertools import zip_longest
from typing import Type

import django
import six
from django.apps import apps
from django.conf import settings
from django.db import connection, ProgrammingError
from django.db.migrations import SeparateDatabaseAndState
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.graph import MigrationGraph

from django_db_views.db_view import DBView, DBMaterializedView, DBViewsRegistry
from django_db_views.operations import (
    ViewRunPython,
    DBViewModelState,
    ViewDropRunPython,
)
from django_db_views.migration_functions import (
    ForwardViewMigration,
    BackwardViewMigration,
    ForwardMaterializedViewMigration,
    BackwardMaterializedViewMigration,
    ForwardViewMigrationBase,
    BackwardViewMigrationBase,
    DropView,
    DropMaterializedView,
    DropViewMigration,
)


class ViewMigrationAutoDetector(MigrationAutodetector):
    """
    We overwritten only _detect_changes function.
    It's almost same code as in regular function,
    we just removed generating other operations, and instead of them added our detection.
    rest methods are fully our code which we use for detection.
    It's detect only view model changes.
    """

    def _detect_changes(self, convert_apps=None, graph=None) -> dict:
        # <START copy paste from MigrationAutodetector, depends on django version>
        if django.VERSION >= (4,):
            self._detect_changes_preparation_django_version_4_and_above(convert_apps)
        else:
            self._detect_changes_preparation_django_below_version_4(convert_apps)
        # <END of copy paste from MigrationAutodetector>

        self.generate_views_operations(graph)
        self.delete_old_views()

        if django.VERSION >= (3, 2):
            # we write custom detect cus views indexes are much more simpler.
            self.old_indexes = set()
            self.new_indexes = set()
            self.detect_index_changes()
            self.drop_indexes()
            self.generate_indexes()

        # <START copy paste from MigrationAutodetector>
        self._sort_migrations()
        self._build_migration_list(graph)
        self._optimize_migrations()

        return self.migrations
        # <END end of copy paste from MigrationAutodetector>

    def _detect_changes_preparation_django_below_version_4(self, convert_apps):
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
            elif al not in self.from_state.real_apps or (
                convert_apps and al in convert_apps
            ):
                if model._meta.proxy:
                    self.new_proxy_keys.append((al, mn))
                else:
                    self.new_model_keys.append((al, mn))

    def _detect_changes_preparation_django_version_4_and_above(self, convert_apps):
        self.generated_operations = {}
        self.altered_indexes = {}
        self.altered_constraints = {}

        # Prepare some old/new state and model lists, separating
        # proxy models and ignoring unmigrated apps.
        self.old_model_keys = set()
        self.old_proxy_keys = set()
        self.old_unmanaged_keys = set()
        self.new_model_keys = set()
        self.new_proxy_keys = set()
        self.new_unmanaged_keys = set()
        for (app_label, model_name), model_state in self.from_state.models.items():
            if not model_state.options.get("managed", True):
                self.old_unmanaged_keys.add((app_label, model_name))
            elif app_label not in self.from_state.real_apps:
                if model_state.options.get("proxy"):
                    self.old_proxy_keys.add((app_label, model_name))
                else:
                    self.old_model_keys.add((app_label, model_name))

        for (app_label, model_name), model_state in self.to_state.models.items():
            if not model_state.options.get("managed", True):
                self.new_unmanaged_keys.add((app_label, model_name))
            elif app_label not in self.from_state.real_apps or (
                convert_apps and app_label in convert_apps
            ):
                if model_state.options.get("proxy"):
                    self.new_proxy_keys.add((app_label, model_name))
                else:
                    self.new_model_keys.add((app_label, model_name))

        self.from_state.resolve_fields_and_relations()
        self.to_state.resolve_fields_and_relations()

    def delete_old_views(self):
        for (
            app_label,
            table_name,
        ), model_state in self.get_previous_view_models_state().items():
            if model_state.table_name not in DBViewsRegistry:
                self.add_operation(
                    app_label,
                    ViewDropRunPython(
                        self.get_drop_migration_class(model_state.base_class)(
                            model_state.table_name, engine=model_state.view_engine
                        ),
                        self.get_backward_migration_class(model_state.base_class)(
                            model_state.view_definition,
                            model_state.table_name,
                            engine=model_state.view_engine,
                        ),
                        atomic=False,
                    ),
                )

    def get_previous_view_models_state(self) -> dict:
        view_models = {}
        for (app_label, table_name), model_state in self.from_state.models.items():
            if isinstance(model_state, DBViewModelState):
                key = (app_label, table_name)
                view_models[key] = model_state
        return view_models

    @staticmethod
    def get_current_view_models():
        view_models = {}
        for app_label, models in apps.all_models.items():
            for model_name, model_class in models.items():
                if model_class._meta.db_table in DBViewsRegistry:
                    key = (app_label, model_name)
                    view_models[key] = model_class
        return view_models

    def is_same_views(self, current: str, new: str) -> bool:
        if not current:
            return False
        s1_words = filter(
            lambda x: len(x) != 0, re.split(pattern="[^a-zA-Z]*", string=current)
        )
        s2_words = filter(
            lambda x: len(x) != 0, re.split(pattern="[^a-zA-Z]*", string=new)
        )
        for w1, w2 in zip_longest(s1_words, s2_words):
            if not w1 or not w2:
                return False
            if w1.lower() != w2.lower():
                return False
        return True

    def generate_views_operations(self, graph: MigrationGraph) -> None:
        view_models = self.get_current_view_models()
        for (app_label, model_name), view_model in view_models.items():
            new_view_definition = self.get_view_definition_from_model(view_model)
            for engine, latest_view_definition in new_view_definition.items():
                current_view_definition = self.get_previous_view_definition_state(
                    graph, app_label, view_model._meta.db_table, engine
                )
                if not self.is_same_views(
                    current_view_definition, latest_view_definition
                ):
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
                            self.get_forward_migration_class(view_model)(
                                latest_view_definition.strip(";"),
                                view_model._meta.db_table,
                                engine=engine,
                            ),
                            self.get_backward_migration_class(view_model)(
                                current_view_definition.strip(";"),
                                view_model._meta.db_table,
                                engine=engine,
                            ),
                            atomic=False,
                        ),
                        dependencies=dependencies,
                    )

    @staticmethod
    def get_forward_migration_class(model) -> Type[ForwardViewMigrationBase]:
        if issubclass(model, DBMaterializedView):
            return ForwardMaterializedViewMigration
        if issubclass(model, DBView):
            return ForwardViewMigration
        else:
            raise NotImplementedError

    @staticmethod
    def get_backward_migration_class(model) -> Type[BackwardViewMigrationBase]:
        if issubclass(model, DBMaterializedView):
            return BackwardMaterializedViewMigration
        if issubclass(model, DBView):
            return BackwardViewMigration
        else:
            raise NotImplementedError

    def get_drop_migration_class(self, model) -> Type[DropViewMigration]:
        if issubclass(model, DBMaterializedView):
            return DropMaterializedView
        elif issubclass(model, DBView):
            return DropView
        else:
            raise NotImplementedError

    @classmethod
    def get_view_definition_from_model(cls, view_model: DBView) -> dict:
        view_definitions = {}
        if callable(view_model.view_definition):
            raw_view_definition = view_model.view_definition()
        else:
            raw_view_definition = view_model.view_definition

        if isinstance(raw_view_definition, dict):
            for engine, definition in raw_view_definition.items():
                view_definitions[engine] = cls.get_cleaned_view_definition_value(
                    definition
                )
        else:
            engine = settings.DATABASES["default"]["ENGINE"]
            view_definitions[engine] = cls.get_cleaned_view_definition_value(
                raw_view_definition
            )
        return view_definitions

    def get_previous_view_definition_state(
        self, graph: MigrationGraph, app_label: str, for_table_name: str, engine: str
    ) -> str:
        nodes = graph.leaf_nodes(app_label)
        last_node = nodes[0] if nodes else None

        while last_node:
            migration = graph.nodes[last_node]
            if migration.operations:
                for operation in migration.operations:
                    if isinstance(operation, ViewRunPython):
                        (
                            table_name,
                            previous_view_engine,
                        ) = self._get_view_identifiers_from_operation(operation)
                        if (
                            table_name == for_table_name
                            and previous_view_engine == engine
                        ):
                            return operation.code.view_definition.strip()
                    elif isinstance(operation, SeparateDatabaseAndState):
                        view_operations = list(
                            filter(
                                lambda op: isinstance(op, ViewRunPython),
                                operation.database_operations,
                            )
                        )
                        if view_operations:
                            assert (
                                len(view_operations) <= 1
                            ), "SeparateDatabaseAndState can't contain more than one ViewRunPython operation"
                            view_operation = view_operations[0]
                            (
                                table_name,
                                previous_view_engine,
                            ) = self._get_view_identifiers_from_operation(
                                view_operation
                            )
                            if (
                                table_name == for_table_name
                                and previous_view_engine == engine
                            ):
                                return view_operation.code.view_definition.strip()
            # right now i get only migrations from the same app.
            app_parents = list(
                sorted(
                    filter(
                        lambda x: x[0] == app_label, graph.node_map[last_node].parents
                    )
                )
            )
            if app_parents:
                last_node = app_parents[-1]
            else:  # if no parents mean we found initial migration
                last_node = None
        return ""

    def _get_view_identifiers_from_operation(self, operation) -> tuple[str, str]:
        table_name = operation.code.table_name
        if hasattr(operation.code, "view_engine") and operation.code.view_engine:
            engine = operation.code.view_engine
        else:
            engine = settings.DATABASES["default"]["ENGINE"]
        return table_name, engine

    @staticmethod
    def get_cleaned_view_definition_value(view_definition: str) -> str:
        assert isinstance(
            view_definition, str
        ), "View definition must be callable and return string or be itself a string."
        return view_definition.strip()

    def get_current_view_definition_from_database(self, table_name: str) -> str:
        """working only with postgres"""
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT pg_get_viewdef('%s')" % table_name)
                current_view_definition = cursor.fetchone()[0].strip()
            except ProgrammingError:  # VIEW NOT EXIST
                current_view_definition = ""
            finally:
                return current_view_definition

    def detect_index_changes(self):
        pass

    def drop_indexes(self):
        pass

    def generate_indexes(self):
        pass
