import os

from django.conf import settings
import environ
from .dynamic_models_fixtures import *  # noqa

env = environ.Env()
env.read_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

pytest_plugins = ()


def pytest_configure():
    """Configure a django settings"""
    postgres_config = {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('POSTGRES_DB'),
                'USER': env('POSTGRES_USER'),
                'PASSWORD': env('POSTGRES_PASSWORD'),
                'HOST': env('POSTGRES_HOST'),
                'PORT': env('POSTGRES_PORT'),
            }
    mysql_config = {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': env('MYSQL_DATABASE'),
                'USER': env('MYSQL_USER'),
                'PASSWORD': env('MYSQL_PASSWORD'),
                'HOST': env('MYSQL_HOST'),
                'PORT': env('MYSQL_PORT'),
                'TEST': {
                    'ENGINE': 'django.db.backends.mysql',
                    'NAME': env('MYSQL_DATABASE'),
                    'USER': env('MYSQL_USER'),
                    'PASSWORD': env('MYSQL_PASSWORD'),
                    'HOST': env('MYSQL_HOST'),
                    'PORT': env('MYSQL_PORT'),
                }
            }
    sqlite = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test-db'
    }

    settings.configure(
        DATABASES={
            "default": postgres_config,
            # engines
            "postgres": postgres_config,
            "mysql": mysql_config,
            "sqlite": sqlite
        },
        INSTALLED_APPS=[
            "django_db_views",
            "tests.test_app"
        ],
    )
