# django-db-views

### How to install?
  - `pip install django-db-views`

### How to use?
   - add `django_db_views` to `INSTALLED_APPS`
   - use `makeviewmigrations` command to create migrations for view models


### How to create view in your database?

- To create your view use DBView class, remember to set view definition attribute.


    from django_db_views.db_view import DBView
    
    class Balance(DBView):

        virtual_card = models.ForeignKey(
            VirtualCard, on_delete=models.DO_NOTHING, related_name='virtual_cards'
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
            managed = False
            db_table = 'virtual_card_balance'


- The view definition must be a string or a callable. 
Callable view definition example:


    view_definition = lambda: str(SomeModel.objects.all().query)


using callable allow you to write view definition using ORM. 

### How view migrations work? 
   - DBView working as regular django model. You can use it in any query. 
   - It's using Django code, view-migrations looks like regular migrations. 
   - It relies on `db_table` names. 
   - `makeviewmigrations` command finds previous migration for view.
      - if there is no such migration then script create a new migration
      - if previous migration exists but no change in `view_definition` is detected nothing is done
      - if previous migration exists, then script will use previous `view_definition` for backward operation, and creates new migration.

Tested with live projects based on Django: 1.11.5, 2.2.10
