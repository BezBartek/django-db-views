from typing import Union, Callable

from django.db import models, connections, DEFAULT_DB_ALIAS
from django.db.models.base import ModelBase

DBViewsRegistry = {}


class DBViewModelBase(ModelBase):
    def __new__(cls, *args, **kwargs):
        new_class = super().__new__(cls, *args, **kwargs)
        assert (
            new_class._meta.managed is False
        ), "For DB View managed must be set to false"
        if not new_class._meta.abstract:
            DBViewsRegistry[new_class._meta.db_table] = new_class
        return new_class


class DBView(models.Model, metaclass=DBViewModelBase):
    """
    Children should define:
        view_definition - define the view, can be callable or attribute (string)
        view definition can be per db engine.
    """

    view_definition: Union[Callable, str, dict]

    class Meta:
        managed = False
        abstract = True


class DBMaterializedView(DBView):
    class Meta:
        managed = False
        abstract = True

    @classmethod
    def refresh(cls, using=None, concurrently=False):
        """
        concurrently option requires an index and postgres db
        """
        using = using or DEFAULT_DB_ALIAS
        with connections[using].cursor() as cursor:
            if concurrently:
                cursor.execute(
                    "REFRESH MATERIALIZED VIEW CONCURRENTLY %s;" % cls._meta.db_table
                )
            else:
                cursor.execute("REFRESH MATERIALIZED VIEW %s;" % cls._meta.db_table)
