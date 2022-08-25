import importlib

import pytest
from django.apps import apps


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
    try:
        yield None
    finally:
        # We delete all dynamically created models
        test_app_models = list(apps.all_models['test_app'].keys())
        for model_name in test_app_models:
            del apps.all_models['test_app'][model_name]
        apps.clear_cache()
