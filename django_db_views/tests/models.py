from django.db import models
from django.utils import timezone
from django_db_views.db_view import DBView


class Question(models.Model):
    text = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "question"


class Choice(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    class Meta:
        db_table = "choice"


class QuestionStat(DBView):
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey(
        "Question", on_delete=models.DO_NOTHING, related_name="question"
    )
    total_choices = models.IntegerField()

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

    class Meta:
        managed = False
        db_table = "question_stat"


class ViewForBackwardCompatibilityCheck(DBView):
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey(
        "Question", on_delete=models.DO_NOTHING, related_name="question"
    )
    total_choices = models.IntegerField()

    view_definition = """
              SELECT
                  row_number() over () as id,
                  q.id as question_id,
                  count(*) as total_choices
              FROM question q
                JOIN choice c on c.question_id = q.id
              GROUP BY q.id
            """

    class Meta:
        managed = False
        db_table = "view_for_backward_compatibility_check"
