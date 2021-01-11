SECRET_KEY = 'fake-key'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test-db'
    }
}
INSTALLED_APPS = [
    'django_db_views',
    'migrations',
    'tests',
]
