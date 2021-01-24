import django
import os

from unittest.mock import patch
from django.apps import apps
from django.conf import settings
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.db.migrations.recorder import MigrationRecorder
from django.db import connections
from django.core.management import call_command
from django.test import TransactionTestCase, override_settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
django.setup()


class MigrationTests(TransactionTestCase):

    def tearDown(self):
        for db in self.databases:
            recorder = MigrationRecorder(connections[db])
            recorder.migration_qs.filter(app='migrations').delete()

    available_apps = ['migrations']

    def assertTableNotExists(self, table, using='default'):
        with connections[using].cursor() as cursor:
            self.assertNotIn(table, connections[using].introspection.table_names(cursor))

    def assertViewExists(self, view, using='default'):
        with connections[using].cursor() as cursor:
            tables = [
                table.name for table in connections[using].introspection.get_table_list(cursor) if table.type == 'v'
            ]
            self.assertIn(view, tables)

    def assertViewNotExists(self, view, using='default'):
        with connections[using].cursor() as cursor:
            tables = [
                table.name for table in connections[using].introspection.get_table_list(cursor) if table.type == 'v'
            ]
            self.assertNotIn(view, tables)

    @override_settings(MIGRATION_MODULES={'migrations': 'migrations.test_basic_view_creation'})
    def test_migrate_successfully_creates_view(self):
        call_command('migrate')
        self.assertViewExists('question_stat')
        self.assertViewExists('view_for_backward_compatibility_check')

    @override_settings(MIGRATION_MODULES={'migrations': 'migrations.test_basic_view_creation'})
    def test_roll_back_successfully_removes_view(self):
        call_command('migrate')
        call_command('migrate', 'migrations', 'zero')
        self.assertViewNotExists('question_stat')
        self.assertViewNotExists('view_for_backward_compatibility_check')


