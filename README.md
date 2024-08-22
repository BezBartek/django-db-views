# django-db-views


[![License](https://img.shields.io/:license-mit-blue.svg)](http://doge.mit-license.org)  
[![PyPi](https://badge.fury.io/py/django-db-views.svg)](https://pypi.org/project/django-db-views/)  
**Django Versions** 2.2 to 4.2+  
**Python Versions** 3.9 to 3.11 


### How to install?
  - `pip install django-db-views`

### What we offer
 - Database views
 - Materialized views
 - views schema migrations 
 - indexing for materialized views (future)
 - database table function (future)

### How to use?
   - add `django_db_views` to `INSTALLED_APPS`
   - use `makeviewmigrations` command to create migrations for view models


### How to create view in your database?

- To create your view use DBView class, remember to set view definition attribute.


   ```python
    from django.db import models
    from django_db_views.db_view import DBView
    
    
    class VirtualCard(models.Model):
        ...
    
    
    class Balance(DBView):

        virtual_card = models.ForeignKey(
            VirtualCard,  # VirtualCard is a regular Django model. 
            on_delete=models.DO_NOTHING, related_name='virtual_cards'
        )
        total_discount = models.DecimalField(max_digits=12, decimal_places=2)
        total_returns = models.DecimalField(max_digits=12, decimal_places=2)
        balance = models.DecimalField(max_digits=12, decimal_places=2)
        
        view_definition = """
            SELECT
                row_number() over () as id,  # Django requires column called id
                virtual_card.id as virtual_card_id,
                sum(...) as total_discount,
            ...
        """
    
        class Meta:
            managed = False  # Managed must be set to False!
            db_table = 'virtual_card_balance'
   ```


- The view definition can be: **str/dict** or a callable which returns **str/dict**. 

   Callable view definition examples:

   ```python
    from django_db_views.db_view import DBViewl
  
    class ExampleView(DBView):
        @staticmethod
        def view_definition():
            #  Note for MySQL users:
            #    In the case of MySQL you might have to use: 
            #    connection.cursor().mogrify(*queryset.query.sql_with_params()).decode() instead of str method to get valid sql statement from Query.
            return str(SomeModel.objects.all().query)  

        # OR
        view_definition = lambda: str(SomeModel.objects.all().query)
        class Meta:
            managed = False 
            db_table = 'example_view'
   ```

   using callable allow you to write view definition using ORM.

- Ensure that you include `managed = False` in the DBView model's Meta class to prevent Django creating it's own migration.

### How view migrations work? 
   - DBView working as regular django model. You can use it in any query. 
   - It's using Django code, view-migrations looks like regular migrations. 
   - It relies on `db_table` names. 
   - `makeviewmigrations` command finds previous migration for view.
      - if there is no such migration then script create a new migration
      - if previous migration exists but no change in `view_definition` is detected nothing is done
      - if previous migration exists, then script will use previous `view_definition` for backward operation, and creates new migration.
      - when run it will check if the current default engine definined in django.settings is the same engine the view was defined with


### Multidatabase support
Yoy can define view_definition as
a dict for multiple engine types.

If you do not pass in an engine and have a str or callable the
engine will be defaulted to the default database defined in django.

It respects --database flag in the migrate command,
So you are able to define a specific view definitions for specific databases using the engine key.
If the key do not match your current database, view migration will be skipped.

Also, feature becomes useful if you use a different engine for local / dev / staging / production.

Example dict view definition:

```python
view_definition = {
    "django.db.backends.sqlite3": """
        SELECT
            row_number() over () as id,
            q.id as question_id,
            count(*) as total_choices
        FROM question q
        JOIN choice c on c.question_id = q.id
        GROUP BY q.id
    """,
    "django.db.backends.postgresql": """
        SELECT
            row_number() over () as id,
            q.id as question_id,
            count(*) as total_choices
        FROM question q
        JOIN choice c on c.question_id = q.id
        GROUP BY q.id
    """,
}
```

### Materialized Views

Just inherit from `DBMaterializedView` instead of regular `DBView`

Materialzied View provide an extra class method to refresh view called `refresh`


### Notes
_Please use the newest version. version 0.1.0 has backward
incompatibility which is solved in version 0.1.1 and higher._
