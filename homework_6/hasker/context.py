"""
Дополнение контекста
"""
from django.db.models import Count
from django.http import HttpRequest

from qna.models import Question

trending_questions_queryset = (Question.objects
                               .prefetch_related("vote_set")
                               .annotate(votes_count=Count("vote"))
                               .order_by("-votes_count")
                               .all())[:5]


def add_context(request: HttpRequest):
    """Добавление топ 5 вопросов в тренды"""
    context = {"trending_questions": trending_questions_queryset,
               "search_text": ""}
    return context
