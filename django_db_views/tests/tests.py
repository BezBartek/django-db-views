import django
import os

from unittest.mock import patch
from django.apps import apps
from django.conf import settings
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.core.management import call_command
from django.test import TransactionTestCase, override_settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'
django.setup()


class MigrateTests(TransactionTestCase):
    @patch('django_db_views.autodetector.ViewMigrationAutoDetector.generate_views_operations')
    def test_makeviewmigrations_calls_generate_views_operations(self, mock_generate_views_operations):
        call_command('makeviewmigrations')
        self.assertTrue(mock_generate_views_operations.called)

    def test_view_definition_with_dict_type(self):
        from django_db_views.autodetector import ViewMigrationAutoDetector
        from django_db_views.tests.models import Balance
        loader = MigrationLoader(None, ignore_no_migrations=True)
        from_state = loader.project_state()
        to_state = ProjectState.from_apps(apps)
        auto_detector = ViewMigrationAutoDetector(from_state=from_state, to_state=to_state)
        Balance.view_definition = {}
        auto_detector.get_view_definition_from_model(Balance)




