import pytest
from django.core.management import call_command

from tests.asserts_utils import is_view_exists


@pytest.fixture(autouse=True)
def backward_compatibility_test_app_settings(settings):
    settings.INSTALLED_APPS += ['tests.backward_compatibility_test_app']
    yield settings
    settings.INSTALLED_APPS.remove('tests.backward_compatibility_test_app')


@pytest.mark.django_db()
@pytest.mark.tag("0.0.9 to 0.0.10")
def test_engine_support_backward_compatibility_migration():
    """Ensures that the initial migration works."""
    assert not is_view_exists("view_for_backward_compatibility_check")
    call_command(
        "migrate", app_label="backward_compatibility_test_app",
        migration_name="0-0-9_to_0-0-10_added_engine_support"
    )
    assert is_view_exists("view_for_backward_compatibility_check")
    call_command(
        "migrate", app_label="backward_compatibility_test_app",
        migration_name="zero"
    )
    assert not is_view_exists("view_for_backward_compatibility_check")
