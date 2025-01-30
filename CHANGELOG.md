# Changelog
Changelogs starts from version 0.1.3

## Unreleased

## Released

### [0.1.10]
- fix no_migrations_teardown at django_db_views_setup fixture

### [0.1.9]
- Add pytest `--no-migrations` support

### [0.1.8]
- Sqlmigrate command shows sql definitions of a view models

### [0.1.7]
- Support for reading ViewRunPython operations from SeparateDatabaseAndState operations

### [0.1.6]
- Adjusted tests to django 4.2

### [0.1.5]
- Fix view_migration_context
- Fix function that generate table hash name, to return lower case strings always 

### [0.1.4]
- Fix broken migration from 0.1.3 version.  https://github.com/BezBartek/django-db-views/issues/20


### [0.1.3]
- Detect and delete removed views or views implementations for specified engines.
- Materialized Views
- Started using project state to track models (Operations defines state_forwards)
- Added view registry to simplify tracking of model changes

### [0.1.2]
- Change log starts from 0.1.3
