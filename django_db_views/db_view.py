from django.db import models


class DBView(models.Model):
    pass

    class Meta:
        abstract = True
