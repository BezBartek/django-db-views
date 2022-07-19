from django.apps import apps
from django.db import models
from django.db.models import F
from django.utils import timezone


def get_declared_class_attributes(cls) -> dict:
  return {key: value for key, value in cls.__dict__.items() if not key.startswith('__')}


def define_model(template_class, parent):
    attributes = get_declared_class_attributes(template_class)
    attrs = {
        **attributes,
        '__module__': 'tests.test_app.models'
    }
    return type(template_class.__name__.replace("Template", ""), (parent,), attrs)


class QuestionTemplate:
    text = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)


class ChoiceTemplate:
    question = models.ForeignKey("Question", on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


# DB Views models (inherit from DBView)
class SimpleViewWithoutDependenciesTemplate:
    identifier = models.IntegerField(primary_key=True)
    name = models.TextField()

    view_definition = """
              Select *
                 From  (values (1, 'dummy_1')
                              ,(2, 'dummy_2')
                       ) A(id, name)
            """

    class Meta:
        managed = False
        db_table = "simple_view_without_dependencies_template"


class RawViewQuestionStatTemplate:
    question = models.ForeignKey(
        "Question", on_delete=models.DO_NOTHING, related_name="question", primary_key=True
    )
    total_choices = models.IntegerField()

    view_definition = """
      SELECT
          row_number() over () as id,
          q.id as question_id,
          count(*) as total_choices
      FROM test_app_question q
        JOIN test_app_choice c on c.question_id = q.id
      GROUP BY q.id
    """

    class Meta:
        managed = False
        db_table = "question_stat"


class QueryViewQuestionStatTemplate:
    question = models.ForeignKey(
        "Question", on_delete=models.DO_NOTHING, related_name="question", primary_key=True
    )
    total_choices = models.IntegerField()

    @staticmethod
    def view_definition():
        return str(
            apps.get_model(
                'test_app', 'Question'
            ).objects.values("id").annotate(total_choices=models.Count("choices"), question_id=F("id")).query
        )

    class Meta:
        managed = False
        db_table = "question_stat"


class MultipleDBRawViewQuestionStatTemplate:
    identifier = models.IntegerField(primary_key=True)
    name = models.TextField()

    view_definition = {
        "django.db.backends.sqlite3": """
            Select 1 as id, "dummy_1" as name
            UNION
            Select 2 AS id, "dummy_2" AS name
        """,
        "django.db.backends.postgresql": """
              Select *
                 From  (values (1, 'dummy_1')
                              ,(2, 'dummy_2')
                       ) A(id, name)
        """,
    }

    class Meta:
        managed = False
        db_table = "question_stat"


class MultipleDBQueryViewQuestionStatTemplate:
    identifier = models.IntegerField(primary_key=True)
    name = models.TextField()

    @staticmethod
    def view_definition():
        queryset = apps.get_model(
                    'test_app', 'Question'
                ).objects.values("id").annotate(total_choices=models.Count("choices"), question_id=F("id"))
        return {
            "django.db.backends.mysql": str(
                queryset.query.get_compiler("mysql").as_sql()[0]
            ),
            "django.db.backends.postgresql": str(
                queryset.query
            )
        }

    class Meta:
        managed = False
        db_table = "question_stat"
