"""
Дополнение контекста
"""
from django.db.models import Count
from django.http import HttpRequest

from qna.models import Question


def add_context(request: HttpRequest):
    """Добавление топ 5 вопросов в тренды"""
    questions = (Question.objects
                 .prefetch_related("vote_set")
                 .annotate(votes_count=Count("vote"))
                 .order_by("-votes_count")
                 .all())[:5]
    context = {"trending_questions": questions,
               "search_text": ""}
    return context
