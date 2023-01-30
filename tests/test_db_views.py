import pytest
from django.apps import apps
from django.core.management import call_command

from django_db_views.db_view import DBViewsRegistry
from tests.asserts_utils import is_view_exists
from tests.decorators import roll_back_schema
from tests.fixturies import temp_migrations_dir, dynamic_models_cleanup  # noqa


@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_make_view_migration_for_db_view_based_on_raw_sql_without_dependencies(
        temp_migrations_dir, SimpleViewWithoutDependencies
):
    assert not (temp_migrations_dir / "0001_initial.py").exists()
    assert not is_view_exists(SimpleViewWithoutDependencies._meta.db_table)
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    call_command("migrate", "test_app")
    assert is_view_exists(SimpleViewWithoutDependencies._meta.db_table)
    assert SimpleViewWithoutDependencies.objects.all().count() == 2
    call_command("migrate", "test_app", "zero")
    assert not is_view_exists(SimpleViewWithoutDependencies._meta.db_table)


@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_make_view_migration_for_db_view_based_on_raw_sql_with_dependencies_on_other_models(
        temp_migrations_dir, Question, Choice, RawViewQuestionStat
):
    assert not (temp_migrations_dir / "0001_initial.py").exists()
    assert not is_view_exists(RawViewQuestionStat._meta.db_table)
    call_command("makemigrations", "test_app")  # make migrations for regular tables
    call_command("makeviewmigrations", "test_app", name="view_migration")  # make migrations for db view
    assert len(temp_migrations_dir.listdir()) == 3, temp_migrations_dir.listdir()
    assert (temp_migrations_dir / "0001_initial.py").exists()
    assert (temp_migrations_dir / "0002_view_migration.py").exists()
    assert "('test_app', '0001_initial')" in (temp_migrations_dir / "0002_view_migration.py").read()
    call_command("migrate", "test_app")
    assert is_view_exists(RawViewQuestionStat._meta.db_table)
    assert RawViewQuestionStat.objects.all().count() == 0
    # define some instances
    question_1 = Question.objects.create(text="question_1")
    question_2 = Question.objects.create(text="question_2")
    Choice.objects.create(question=question_1, text="choice_1", votes=10)
    Choice.objects.create(question=question_1, text="choice_2", votes=10)
    Choice.objects.create(question=question_2, text="choice_1", votes=10)
    # check whether the model works correctly
    assert RawViewQuestionStat.objects.all().count() == 2
    assert RawViewQuestionStat.objects.all().order_by("question").first().question.text == question_1.text


@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_make_view_migration_for_db_view_based_on_queryset_with_dependencies_on_other_models(
        temp_migrations_dir, Question, Choice, QueryViewQuestionStat
):
    assert not (temp_migrations_dir / "0001_initial.py").exists()
    assert not is_view_exists(QueryViewQuestionStat._meta.db_table)
    call_command("makemigrations", "test_app")  # make migrations for regular tables
    call_command("makeviewmigrations", "test_app", name="view_migration")  # make migrations for db view
    assert len(temp_migrations_dir.listdir()) == 3
    assert (temp_migrations_dir / "0001_initial.py").exists()
    assert (temp_migrations_dir / "0002_view_migration.py").exists()
    assert "('test_app', '0001_initial')" in (temp_migrations_dir / "0002_view_migration.py").read()
    call_command("migrate", "test_app")
    assert is_view_exists(QueryViewQuestionStat._meta.db_table)
    assert QueryViewQuestionStat.objects.all().count() == 0
    # define some instances
    question_1 = Question.objects.create(text="question_1")
    question_2 = Question.objects.create(text="question_2")
    Choice.objects.create(question=question_1, text="choice_1", votes=10)
    Choice.objects.create(question=question_1, text="choice_2", votes=10)
    Choice.objects.create(question=question_2, text="choice_1", votes=10)
    # check whether the model works correctly
    assert QueryViewQuestionStat.objects.all().count() == 2
    assert QueryViewQuestionStat.objects.all().order_by("question").first().question.text == question_1.text


@pytest.mark.django_db(databases=['postgres', 'sqlite'], transaction=True)
@pytest.mark.parametrize("database", ['postgres', 'sqlite'])
@roll_back_schema
def test_make_view_migration_for_db_raw_view_with_multiple_databases_support(
        temp_migrations_dir, database, MultipleDBRawView
):
    assert not (temp_migrations_dir / "0001_initial.py").exists()
    assert not is_view_exists(MultipleDBRawView._meta.db_table, using=database)
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    call_command("migrate", "test_app", database=database)
    assert is_view_exists(MultipleDBRawView._meta.db_table, using=database)
    assert MultipleDBRawView.objects.using(database).all().count() == 2


@pytest.mark.django_db(databases=['default', 'postgres', 'mysql'], transaction=True)
@pytest.mark.parametrize("database", ['postgres', 'mysql'])
@roll_back_schema
def test_make_view_migration_for_db_queryset_view_with_multiple_databases_support(
        temp_migrations_dir, database, Question, Choice, MultipleDBQueryViewQuestionStat
):
    assert not (temp_migrations_dir / "0001_initial.py").exists()
    assert not is_view_exists(MultipleDBQueryViewQuestionStat._meta.db_table, using=database)
    call_command("makemigrations", "test_app")
    call_command("makeviewmigrations", "test_app")
    call_command("makemigrations", "test_app")
    assert len(temp_migrations_dir.listdir()) == 3, temp_migrations_dir.listdir()
    assert (temp_migrations_dir / "0001_initial.py").exists()
    call_command("migrate", "test_app", database=database)
    assert is_view_exists(MultipleDBQueryViewQuestionStat._meta.db_table, using=database)
    assert MultipleDBQueryViewQuestionStat.objects.using(database).all().count() == 0
    call_command("migrate", "test_app", "zero", database=database)
    assert not is_view_exists(MultipleDBQueryViewQuestionStat._meta.db_table, using=database)


@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_move_up_and_down_through_simple_view_stages(
        temp_migrations_dir, SimpleViewWithoutDependencies
):
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    # made changes
    apps.all_models['test_app']["simpleviewwithoutdependencies"].view_definition = """
              Select *
                 From  (values (3, 'dummy_3')) A(id, name)
            """
    call_command("makeviewmigrations", "test_app", name="second_view_migration")
    assert (temp_migrations_dir / "0002_second_view_migration.py").exists()
    # no changes
    call_command("makeviewmigrations", "test_app", name="third_view_migration")
    assert not (temp_migrations_dir / "0003_third_view_migration.py").exists()
    assert len(temp_migrations_dir.listdir()) == 3
    # we are on stage 2
    call_command("migrate", "test_app")
    assert is_view_exists(SimpleViewWithoutDependencies._meta.db_table)
    assert SimpleViewWithoutDependencies.objects.all().count() == 1
    # go back to stage 1
    call_command("migrate", "test_app", "0001")
    assert is_view_exists(SimpleViewWithoutDependencies._meta.db_table)
    assert SimpleViewWithoutDependencies.objects.all().count() == 2
    # move to stag 1
    call_command("migrate", "test_app", "zero")
    assert not is_view_exists(SimpleViewWithoutDependencies._meta.db_table)


@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_drop_view(
        temp_migrations_dir, SimpleViewWithoutDependencies
):
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    del apps.all_models['test_app'][SimpleViewWithoutDependencies.__name__.lower()]
    apps.clear_cache()
    DBViewsRegistry.pop(SimpleViewWithoutDependencies._meta.db_table)
    call_command("makeviewmigrations", "test_app", name="delete_view")
    assert (temp_migrations_dir / "0002_delete_view.py").exists()
    migrations = (temp_migrations_dir / "0002_delete_view.py").read()
    assert "DropView" in migrations
    assert "ViewDropRunPython" in migrations
    # move forward and backward
    call_command("migrate", "test_app", "0001")
    assert is_view_exists(SimpleViewWithoutDependencies._meta.db_table)
    call_command("migrate", "test_app")
    assert not is_view_exists(SimpleViewWithoutDependencies._meta.db_table)
    call_command("migrate", "test_app", "0001")
    assert is_view_exists(SimpleViewWithoutDependencies._meta.db_table)


@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_drop_view_and_update_existing_view_in_same_migration(
        temp_migrations_dir, SimpleViewWithoutDependencies, SecondSimpleViewWithoutDependencies
):
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    # Delete existing model
    del apps.all_models['test_app'][SecondSimpleViewWithoutDependencies.__name__.lower()]
    apps.clear_cache()
    DBViewsRegistry.pop(SecondSimpleViewWithoutDependencies._meta.db_table)
    # Modify existing model
    apps.all_models['test_app']["simpleviewwithoutdependencies"].view_definition = """
        Select *
         From  (values (3, 'dummy_3')) A(id, name)
    """
    # Run migration
    call_command("makeviewmigrations", "test_app", name="delete_view_and_update_view")
    assert (temp_migrations_dir / "0002_delete_view_and_update_view.py").exists()
    migrations = (temp_migrations_dir / "0002_delete_view_and_update_view.py").read()
    assert "DropView" in migrations
    assert "ViewDropRunPython" in migrations
    assert "ViewRunPython" in migrations


@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_drop_view_and_update_existing_view_in_next_migration(
        temp_migrations_dir, SimpleViewWithoutDependencies, SecondSimpleViewWithoutDependencies
):
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    # Delete existing model
    del apps.all_models['test_app'][SecondSimpleViewWithoutDependencies.__name__.lower()]
    apps.clear_cache()
    DBViewsRegistry.pop(SecondSimpleViewWithoutDependencies._meta.db_table)
    # Run migration
    call_command("makeviewmigrations", "test_app", name="delete_view")
    assert (temp_migrations_dir / "0002_delete_view.py").exists()
    migrations = (temp_migrations_dir / "0002_delete_view.py").read()
    assert "DropView" in migrations
    assert "ViewDropRunPython" in migrations
    assert "ViewRunPython" not in migrations
    # Generate model representaions
    call_command("makemigrations", "test_app", name="create_models")
    # Modify existing model
    apps.all_models['test_app']["simpleviewwithoutdependencies"].view_definition = """
      Select *
         From  (values (3, 'dummy_3')) A(id, name)
    """
    call_command("makeviewmigrations", "test_app", name="update_view")
    assert (temp_migrations_dir / "0004_update_view.py").exists()
    migrations = (temp_migrations_dir / "0004_update_view.py").read()
    assert "ViewRunPython" in migrations
    assert "DropView" not in migrations


@pytest.mark.django_db(databases=['sqlite', 'postgres'], transaction=True)
@pytest.mark.parametrize("database", ['postgres', 'sqlite'])
@roll_back_schema
def test_drop_view_multiple_engines(
        temp_migrations_dir, database, MultipleDBRawView
):
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    del apps.all_models['test_app'][MultipleDBRawView.__name__.lower()]
    apps.clear_cache()
    DBViewsRegistry.pop(MultipleDBRawView._meta.db_table)
    call_command("makeviewmigrations", "test_app", name="delete_view")
    assert (temp_migrations_dir / "0002_delete_view.py").exists()
    migrations = (temp_migrations_dir / "0002_delete_view.py").read()
    # both migrations are inside.
    assert "engine='django.db.backends.sqlite3" in migrations
    assert "engine='django.db.backends.postgresql" in migrations
    call_command("migrate", "test_app", "0001", database=database)
    assert is_view_exists(MultipleDBRawView._meta.db_table, using=database)
    call_command("migrate", "test_app", database=database)
    assert not is_view_exists(MultipleDBRawView._meta.db_table, using=database)
    call_command("migrate", "test_app", "0001", database=database)
    assert is_view_exists(MultipleDBRawView._meta.db_table, using=database)
