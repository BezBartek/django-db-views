import sys

from django.apps import apps
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.core.management.commands.makemigrations import Command as MakemigrationsCommand

from django_db_views.autodetector import ViewMigrationAutoDetector


class ViewMigrationsCommand(MakemigrationsCommand):
    help = "Creates new database view migration(s) for apps."

    def add_arguments(self, parser):
        """"
            Not support all operations like makemigrations command, part of them have no sens here, like no-input or empty.
        """
        parser.add_argument(
            'args', metavar='app_label', nargs='*',
            help='Specify the app label(s) to create migrations for.',
        )   # Working
        parser.add_argument(
            '--dry-run', action='store_true', dest='dry_run', default=False,
            help="Just show what migrations would be made; don't actually write them.",
        )   # Working
        parser.add_argument(
            '--merge', action='store_true', dest='merge', default=False,
            help="Enable fixing of migration conflicts.",
        )   # we need that?
        parser.add_argument(
            '-n', '--name', action='store', dest='name', default=None,
            help="Use this name for migration file(s).",
        )   # Working
        parser.add_argument(
            '-e', '--exit', action='store_true', dest='exit_code', default=False,
            help='Exit with error code 1 if no changes needing migrations are found. '
                 'Deprecated, use the --check option instead.',
        )   # we need that?
        parser.add_argument(
            '--check', action='store_true', dest='check_changes',
            help='Exit with a non-zero status if model changes are missing migrations.',
        )   # we need that?

    def handle(self, *app_labels, **options):
        self.verbosity = options['verbosity']
        self.dry_run = options['dry_run']
        self.merge = options['merge']
        self.migration_name = options['name']
        self.exit_code = options['exit_code']
        check_changes = options['check_changes']

        # validation
        self.validate_applications(app_labels)

        # load migrations
        loader = MigrationLoader(None, ignore_no_migrations=True)

        from_state = loader.project_state()
        to_state = ProjectState.from_apps(apps)

        autodetector = ViewMigrationAutoDetector(
            from_state,
            to_state,
        )

        changes = autodetector.changes(
            graph=loader.graph,
            trim_to_apps=app_labels or None,
            convert_apps=app_labels or None,
            migration_name=self.migration_name,
        )

        if changes:
            self.stdout.write("Changes detected.")
            self.write_migration_files(changes)
        else:
            self.stdout.write("No changes detected.")

    # def wrap_migration_names(self):
    #     for app_name, migrations in self.migrations.items():
    #         for migration in migrations:
    #             migration.name = 'db_view_{}'.format(migration.operations[0].code.table_name)

    def validate_applications(self, app_labels: str):
        app_labels = set(app_labels)
        has_bad_labels = False
        for app_label in app_labels:
            try:
                apps.get_app_config(app_label)
            except LookupError as err:
                self.stderr.write(str(err))
                has_bad_labels = True
        if has_bad_labels:
            sys.exit(2)


Command = ViewMigrationsCommand
