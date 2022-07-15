from django.db import models

from django_db_views.db_view import DBView


class ViewForBackwardCompatibilityCheck(DBView):
    id = models.AutoField(primary_key=True)
    name = models.TextField()

    view_definition = """
              Select *
                 From  (values (1, 'dummy_1')
                              ,(2, 'dummy_2')
                       ) A(id, name)
            """

    class Meta:
        app_label = ''
        managed = False
        db_table = "view_for_backward_compatibility_check"
