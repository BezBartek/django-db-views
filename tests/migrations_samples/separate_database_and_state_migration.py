from django.db import migrations, models
import django_db_views.migration_functions
import django_db_views.operations


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                django_db_views.operations.ViewRunPython(
                    code=django_db_views.migration_functions.ForwardViewMigration(
                        "Select *\n                 From  (values (1, 'dummy_1')\n                              ,(2, 'dummy_2')\n                       ) A(id, name)",
                        'test_app_simpleviewwithoutdependencies', engine='django.db.backends.postgresql'),
                    reverse_code=django_db_views.migration_functions.BackwardViewMigration('',
                                                                                           'test_app_simpleviewwithoutdependencies',
                                                                                           engine='django.db.backends.postgresql'),
                    atomic=False,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='SimpleViewWithoutDependencies',
                    fields=[
                        ('identifier', models.IntegerField(primary_key=True, serialize=False)),
                        ('name', models.TextField()),
                    ],
                    options={
                        'abstract': False,
                        'managed': False,
                    },
                ),
            ],
        )
    ]
