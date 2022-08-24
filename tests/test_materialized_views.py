import pytest
from django.core.management import call_command

from tests.asserts_utils import is_view_exists
from tests.decorators import roll_back_schema
from tests.fixturies import temp_migrations_dir, dynamic_models_cleanup  # noqa


@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_materialized_db_view_based_on_raw_sql_without_dependencies(
        temp_migrations_dir, SimpleMaterializedViewWithoutDependencies
):
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    call_command("migrate", "test_app")
    assert is_view_exists(SimpleMaterializedViewWithoutDependencies._meta.db_table)
    assert SimpleMaterializedViewWithoutDependencies.objects.all().count() == 1
    current_date_time_from_view_call_1 = SimpleMaterializedViewWithoutDependencies.objects.get().current_date_time
    current_date_time_from_view_call_2 = SimpleMaterializedViewWithoutDependencies.objects.get().current_date_time
    assert current_date_time_from_view_call_1 == current_date_time_from_view_call_2
    # regular refresh
    SimpleMaterializedViewWithoutDependencies.refresh()
    current_date_time_from_view_call_3 = SimpleMaterializedViewWithoutDependencies.objects.get().current_date_time
    assert current_date_time_from_view_call_1 != current_date_time_from_view_call_3
    # backward migration
    call_command("migrate", "test_app", "zero")
    assert not is_view_exists(SimpleMaterializedViewWithoutDependencies._meta.db_table)


@pytest.mark.skip(reason="Future feature.")
@pytest.mark.django_db(transaction=True)
@roll_back_schema
def test_materialized_db_view_based_on_raw_sql_with_indexes(
        temp_migrations_dir, SimpleMaterializedViewWithIndex
):
    call_command("makeviewmigrations", "test_app")
    assert (temp_migrations_dir / "0001_initial.py").exists()
    call_command("migrate", "test_app")
    assert is_view_exists(SimpleMaterializedViewWithIndex._meta.db_table)
    assert SimpleMaterializedViewWithIndex.objects.all().count() == 1
    current_date_time_from_view_call_1 = SimpleMaterializedViewWithIndex.objects.get().current_date_time
    current_date_time_from_view_call_2 = SimpleMaterializedViewWithIndex.objects.get().current_date_time
    assert current_date_time_from_view_call_1 == current_date_time_from_view_call_2
    # regular refresh
    SimpleMaterializedViewWithIndex.refresh()
    current_date_time_from_view_call_3 = SimpleMaterializedViewWithIndex.objects.get().current_date_time
    assert current_date_time_from_view_call_1 != current_date_time_from_view_call_3
    # regular refresh concurrently
    SimpleMaterializedViewWithIndex.refresh(concurrently=True)
    current_date_time_from_view_call_4 = SimpleMaterializedViewWithIndex.objects.get().current_date_time
    assert current_date_time_from_view_call_3 != current_date_time_from_view_call_4
    # backward migration
    call_command("migrate", "test_app", "zero")
    assert not is_view_exists(SimpleMaterializedViewWithIndex._meta.db_table)
