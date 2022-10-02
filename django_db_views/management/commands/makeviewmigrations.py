import sys

from django.apps import apps
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.questioner import InteractiveMigrationQuestioner
from django.db.migrations.state import ProjectState
from django.core.management.commands.makemigrations import Command as MakemigrationsCommand

from django_db_views.autodetector import ViewMigrationAutoDetector
from django_db_views.context_manager import view_migration_context


class Command(MakemigrationsCommand):
    help = "Creates new database view migration(s) for apps."

    def add_arguments(self, parser):
        """"
            Not support all operations like makemigrations command,
            part of them have no sens here, like no-input or empty.
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
            '--no-header', action='store_false', dest='include_header',
            help='Do not add header comments to new migration file(s). (working only with Django 2.2)',
        )
        parser.add_argument(
            '--check', action='store_true', dest='check_changes',
            help='Exit with a non-zero status if model changes are missing migrations.',
        )   # we need that?
        parser.add_argument(
            "--scriptable",
            action="store_true",
            dest="scriptable",
            help=(
                "Divert log output and input prompts to stderr, writing only "
                "paths of generated migration files to stdout."
            ),
        )

    @view_migration_context()
    def handle(self, *app_labels, **options):
        # get supported options.
        self.written_files = []
        self.verbosity = options['verbosity']
        self.dry_run = options['dry_run']
        self.merge = options['merge']
        self.migration_name = options['name']
        self.include_header = options['include_header']
        self.scriptable = options['scriptable']
        check_changes = options['check_changes']

        # validation application labels
        app_labels = set(app_labels)
        self.validate_applications(app_labels)

        # we don't check conflicts as regular makemigrations command.
        # we don't check if any migrations are applied before their dependencies as regular makemigrations command.

        # load migrations using same loader as in regular command
        loader = MigrationLoader(None, ignore_no_migrations=True)

        from_state = loader.project_state()
        to_state = ProjectState.from_apps(apps)

        # overwritten autodetector. They detect only view changes.
        autodetector = ViewMigrationAutoDetector(
            from_state,
            to_state,
            questioner=InteractiveMigrationQuestioner(specified_apps=app_labels, dry_run=self.dry_run)
        )

        changes = autodetector.changes(
            graph=loader.graph,
            trim_to_apps=app_labels or None,
            convert_apps=app_labels or None,
            migration_name=self.migration_name,
        )

        # it's copy paste from make migration command
        if not changes:
            # No changes? Tell them.
            if self.verbosity >= 1:
                if len(app_labels) == 1:
                    self.stdout.write("No changes detected in app '%s'" % app_labels.pop())
                elif len(app_labels) > 1:
                    self.stdout.write("No changes detected in apps '%s'" % ("', '".join(app_labels)))
                else:
                    self.stdout.write("No changes detected")

        else:
            self.write_migration_files(changes)
            if check_changes:
                sys.exit(1)

    def validate_applications(self, app_labels: set):
        """it's copy paste from make migration command"""
        has_bad_labels = False
        for app_label in app_labels:
            try:
                apps.get_app_config(app_label)
            except LookupError as err:
                self.stderr.write(str(err))
                has_bad_labels = True
        if has_bad_labels:
            sys.exit(2)
