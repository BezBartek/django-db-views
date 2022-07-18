import importlib

import pytest
from django.apps import apps
from django.core.management import call_command

from tests.asserts import is_view_exists


@pytest.fixture(autouse=True, scope='function')
def temp_migrations_dir(settings, tmpdir, mocker):
    migrations_dir = tmpdir.mkdir("migrations")
    init_file = (migrations_dir / "__init__.py")
    init_file.write_text("", encoding="utf-8")
    mocker.patch("django.db.migrations.writer.MigrationWriter.basedir", migrations_dir.strpath)

    def new_module_import(module_name):
        if module_name == 'tests.test_app.migrations':
            spec = importlib.util.spec_from_file_location(module_name, init_file)
            return importlib.util.module_from_spec(spec)
        elif 'tests.test_app.migrations' in module_name:
            spec = importlib.util.spec_from_file_location(module_name, migrations_dir / f"{module_name.split('.')[-1]}.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        return importlib.import_module(module_name)
    mocker.patch(
        "django.db.migrations.loader.import_module",
        new_module_import
    )
    return migrations_dir


@pytest.fixture(autouse=True, scope='function')
def dynamic_models_cleanup():
    yield None
    # We delete all dynamically created models
    test_app_models = list(apps.all_models['test_app'].keys())
    for model_name in test_app_models:
        del apps.all_models['test_app'][model_name]
    apps.clear_cache()


@pytest.mark.django_db()
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


@pytest.mark.django_db()
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


@pytest.mark.django_db()
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
def test_make_view_migration_for_db_raw_view_with_multiple_databases_support(
        temp_migrations_dir, database, MultipleDBRawViewQuestionStat
):
    assert not (temp_migrations_dir / "0001_initial.py").exists()
    assert not is_view_exists(MultipleDBRawViewQuestionStat._meta.db_table, using=database)
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    call_command("migrate", "test_app", database=database)
    assert is_view_exists(MultipleDBRawViewQuestionStat._meta.db_table, using=database)
    assert MultipleDBRawViewQuestionStat.objects.using(database).all().count() == 2
    call_command("migrate", "test_app", "zero", database=database) # after transactions tests we have to clean up.


@pytest.mark.django_db(databases=['default', 'postgres', 'mysql'], transaction=True)
@pytest.mark.parametrize("database", ['postgres', 'mysql'])
def test_make_view_migration_for_db_queryset_view_with_multiple_databases_support(
        temp_migrations_dir, database, Question, Choice, MultipleDBQueryViewQuestionStat
):
    assert not (temp_migrations_dir / "0001_initial.py").exists()
    assert not is_view_exists(MultipleDBQueryViewQuestionStat._meta.db_table, using=database)
    call_command("makemigrations", "test_app")
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    call_command("migrate", "test_app", database=database)
    assert is_view_exists(MultipleDBQueryViewQuestionStat._meta.db_table, using=database)
    assert MultipleDBQueryViewQuestionStat.objects.using(database).all().count() == 0
    call_command("migrate", "test_app", "zero", database=database)
    assert not is_view_exists(MultipleDBQueryViewQuestionStat._meta.db_table, using=database)
    call_command("migrate", "test_app", "zero", database=database) # after transactions tests we have to clean up.


@pytest.mark.django_db()
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
