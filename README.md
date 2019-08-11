# django-db-views

### How to use?
   - add to installed apps
   - use **makeviewmigrations** command to create migrations for view models


### How to create view in your database?

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
                row_number() over () as id,
                virtual_card.id as virtual_card_id,
                sum(usage.discount_amount) as total_discount,
            ...
        """
    
        class Meta:
            managed = False
            db_table = 'offerings_coupon_balance'

### How view migrations work?
   - It's using Django code, migrate looks like regular migration. 
   - It's relies on db_table names. 
   - Our command find previous migration for table.
      - if there is no such migration, than they create new migration
      - if previous migration exist, than script will use previous view_definition for backward operation, and create new migration.

Tested which live project based on Django 1.11.5
