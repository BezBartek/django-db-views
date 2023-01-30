import pytest
from django.db import models

from tests.test_app.models import QuestionTemplate, SimpleViewWithoutDependenciesTemplate, ChoiceTemplate, \
    RawViewQuestionStatTemplate, QueryViewQuestionStatTemplate, MultipleDBRawViewTemplate, \
    MultipleDBQueryViewQuestionStatTemplate, SimpleMaterializedViewWithoutDependenciesTemplate, \
    SimpleMaterializedViewWithIndexTemplate, SecondSimpleViewWithoutDependenciesTemplate


def define_model(template_class, parent):
    attributes = get_declared_class_attributes(template_class)
    attrs = {
        **attributes,
        '__module__': 'tests.test_app.models'
    }
    return type(template_class.__name__.replace("Template", ""), (parent,), attrs)


def get_declared_class_attributes(cls) -> dict:
  return {key: value for key, value in cls.__dict__.items() if not key.startswith('__')}


@pytest.fixture
def Question():
    return define_model(QuestionTemplate, models.Model)


@pytest.fixture()
def Choice():
    return define_model(ChoiceTemplate, models.Model)


@pytest.fixture
def SimpleViewWithoutDependencies():
    from django_db_views.db_view import DBView
    return define_model(SimpleViewWithoutDependenciesTemplate, DBView)


@pytest.fixture
def SecondSimpleViewWithoutDependencies():
    from django_db_views.db_view import DBView
    return define_model(SecondSimpleViewWithoutDependenciesTemplate, DBView)


@pytest.fixture
def RawViewQuestionStat():
    from django_db_views.db_view import DBView
    return define_model(RawViewQuestionStatTemplate, DBView)


@pytest.fixture
def QueryViewQuestionStat():
    from django_db_views.db_view import DBView
    return define_model(QueryViewQuestionStatTemplate, DBView)


@pytest.fixture
def MultipleDBRawView():
    from django_db_views.db_view import DBView
    return define_model(MultipleDBRawViewTemplate, DBView)


@pytest.fixture
def MultipleDBQueryViewQuestionStat():
    from django_db_views.db_view import DBView
    return define_model(MultipleDBQueryViewQuestionStatTemplate, DBView)


@pytest.fixture
def SimpleMaterializedViewWithoutDependencies():
    from django_db_views.db_view import DBMaterializedView
    return define_model(SimpleMaterializedViewWithoutDependenciesTemplate, DBMaterializedView)


@pytest.fixture
def SimpleMaterializedViewWithIndex():
    from django_db_views.db_view import DBMaterializedView
    return define_model(SimpleMaterializedViewWithIndexTemplate, DBMaterializedView)
