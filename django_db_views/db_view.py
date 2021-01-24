from django.db import models


class DBView(models.Model):
    """
        Children should define:
            view_definition - define the view, can be callable or attribute (string)
            view definition can be per db engine.
    """
    pass

    class Meta:
        abstract = True
