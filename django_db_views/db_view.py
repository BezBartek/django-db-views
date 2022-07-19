from typing import Union, Callable

from django.db import models, connections, DEFAULT_DB_ALIAS


class DBView(models.Model):
    """
        Children should define:
            view_definition - define the view, can be callable or attribute (string)
            view definition can be per db engine.
    """
    view_definition: Union[Callable, str, dict]

    class Meta:
        abstract = True


class DBMaterializedView(DBView):
    class Meta:
        abstract = True

    @classmethod
    def refresh(cls, using=None, concurrently=False):
        """
        concurrently option requires an index and postgres db
        """
        using = using or DEFAULT_DB_ALIAS
        with connections[using].cursor() as cursor:
            if concurrently:
                cursor.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY %s;" % cls._meta.db_table)
            else:
                cursor.execute("REFRESH MATERIALIZED VIEW %s;" % cls._meta.db_table)
