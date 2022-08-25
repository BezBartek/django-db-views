import functools
from django.core.management import call_command


def roll_back_schema(test_function):
    @functools.wraps(test_function)
    def decorated_test(*args, **kwargs):
        try:
            test_function(*args, **kwargs)
        finally:
            call_command("migrate", "test_app", "zero", database=kwargs.get("database", "default"))
    return decorated_test
