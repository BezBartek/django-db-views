import pytest
from django.db import models

from tests.test_app.models import define_model, QuestionTemplate, SimpleViewWithoutDependenciesTemplate, ChoiceTemplate, \
    RawViewQuestionStatTemplate, QueryViewQuestionStatTemplate, MultipleDBRawViewQuestionStatTemplate, \
    MultipleDBQueryViewQuestionStatTemplate


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
def RawViewQuestionStat():
    from django_db_views.db_view import DBView
    return define_model(RawViewQuestionStatTemplate, DBView)


@pytest.fixture
def QueryViewQuestionStat():
    from django_db_views.db_view import DBView
    return define_model(QueryViewQuestionStatTemplate, DBView)


@pytest.fixture
def MultipleDBRawViewQuestionStat():
    from django_db_views.db_view import DBView
    return define_model(MultipleDBRawViewQuestionStatTemplate, DBView)


@pytest.fixture
def MultipleDBQueryViewQuestionStat():
    from django_db_views.db_view import DBView
    return define_model(MultipleDBQueryViewQuestionStatTemplate, DBView)
