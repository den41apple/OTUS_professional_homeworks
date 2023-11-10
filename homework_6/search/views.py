from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlencode

from qna.models import Question
from qna.views import IndexView


class SearchView(IndexView):
    template_name = "search/search.html"

    def get_queryset(self):
        self._search_text = search_text = self.request.GET.get("q")
        if not search_text:
            self._header = "Search result"
            return Question.objects.all()[:0]

        search_text = search_text.lower()
        if "tag:" not in search_text:
            self._header = "Search result"
            questions = self._get_text_queryset(search_text)
        else:
            self._header = "Tag result"
            questions = self._get_tag_queryset(search_text)
        return questions

    def _get_common_queryset(self) -> QuerySet:
        """
        Часть запроса одинаковая для обоих случаев
        """
        questions = (Question.objects
                     .select_related("author")
                     .select_related("author__profile")
                     .prefetch_related("answer_set")
                     .prefetch_related("vote_set")
                     .prefetch_related("tag")
                     .annotate(votes_count=Count("vote"))
                     .order_by("-votes_count", "-created_at"))
        return questions

    def _get_text_queryset(self, search_text: str) -> QuerySet:
        """Возвращает поиск по тексту"""
        questions = self._get_common_queryset()
        questions = (questions
                     .filter(Q(title__icontains=search_text)
                             | Q(text__icontains=search_text)
                             | Q(answer__text__icontains=search_text))
                     .all())
        return questions

    def _get_tag_queryset(self, search_text: str) -> QuerySet:
        """
        Возвращает поиск по тэгам
        """
        tag = search_text.lower().replace("tag:", "").strip()
        questions = self._get_common_queryset()
        questions = (questions
                     .filter(tag__text__iexact=tag)
                     .all())
        return questions

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # Добавим значение в строку поиска
        context_data.update(search_text=self._search_text,
                            header=self._header)
        return context_data

    def post(self, request, *args, **kwargs):
        # Извлечение текста поиска
        search_text = self.request.POST.get("search_text", '')
        path = reverse("search:search", )
        query_params = urlencode({"q": search_text})
        path = path + f"?{query_params}"
        return HttpResponseRedirect(path)
