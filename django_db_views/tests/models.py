from django.db import models
from django_db_views.db_view import DBView


class Balance(DBView):
    virtual_card = models.ForeignKey(
        'VirtualCard', on_delete=models.DO_NOTHING, related_name='virtual_cards'
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


class VirtualCard(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80, blank=False)

    class Meta:
        managed = True
        db_table = 'virtual_card'
