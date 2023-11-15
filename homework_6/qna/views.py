import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Count, QuerySet
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import ListView, FormView, CreateView

from .forms import AskForm, QuestionDetailForm
from .models import Question, Tag, Answer, Vote
from .utils import make_pagination


class IndexView(ListView):
    template_name = "qna/index.html"
    _sort_type = "new"
    questions_on_page = 20

    def get_queryset(self):
        sort_type = self.request.GET.get("sort", "new")
        self._sort_type = "new" if sort_type != "hot" else "hot"
        order_by = "-votes_count" if self._sort_type == "hot" else "-created_at"
        questions = (Question.objects
                     .prefetch_related("vote_set")
                     .prefetch_related("answer_set")
                     .select_related("author")
                     .select_related("author__profile")
                     .prefetch_related("tag")
                     .annotate(votes_count=Count("vote"))
                     .order_by(order_by)
                     .all())
        return questions

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data()
        question_list: QuerySet = kwargs['question_list']
        current_page = int(self.request.GET.get("page", 1))
        pages = make_pagination(queryset=question_list,
                                current_page=current_page,
                                questions_on_page=self.questions_on_page)
        questions = question_list[pages['range']]
        kwargs.update(sort_type=self._sort_type,
                      questions=questions,
                      pages=pages)
        return kwargs


class AskQuestionView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = AskForm
    template_name = "qna/ask.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        # Отключим кнопку спросить вопрос справа над трендами
        context_data.update(disable_ask_button=True)
        return context_data

    def form_valid(self, form):
        user: AbstractUser = self.request.user
        title = form.cleaned_data.get("title")
        text = form.cleaned_data.get("text")
        tags = form.cleaned_data.get("tags")
        tag_texts = [el.replace(" ", "") for el in tags.split(",")]
        with transaction.atomic():
            tags = self._create_tags(tag_texts=tag_texts)
            question = Question(title=title,
                                text=text,
                                author=user)
            question.save()
            question.tag.set(tags)
        path = reverse("qna:question", kwargs={"pk": question.pk})
        return HttpResponseRedirect(path)

    def _create_tags(self, tag_texts: list) -> list[Tag]:
        tags = []
        for tag_text in tag_texts:
            if not tag_text:
                continue
            tag = Tag.objects.filter(text=tag_text).first()
            if not tag:
                tag = Tag(text=tag_text)
                tag.save()
            tags.append(tag)
        return tags


class QuestionDetailView(LoginRequiredMixin, FormView):
    form_class = QuestionDetailForm
    template_name = "qna/question_detail.html"

    def get_success_url(self):
        path = self.request.path
        context_data = self.get_context_data()
        last_page = context_data.get("pages", {}).get("_last_page")
        if last_page:
            query_params = urlencode({"page": last_page})
            path = path + f"?{query_params}"
        return path

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        current_page = int(self.request.GET.get("page", 1))
        pk = self.kwargs.get("pk")
        question = (Question.objects
                    .prefetch_related("vote_set")
                    .select_related("author")
                    .select_related("author__profile")
                    .prefetch_related("tag")
                    .filter(pk=pk)
                    .first())
        answers = (Answer.objects
                   .filter(question=question)
                   .prefetch_related("vote_set")
                   .select_related("author")
                   .select_related("author__profile")
                   .select_related("question")
                   .order_by("-is_correct")
                   .all())
        correct_answer = [answ for answ in answers if answ.is_correct is True]
        correct_answer = correct_answer[0] if correct_answer else None
        pages = make_pagination(queryset=answers,
                                questions_on_page=30,
                                current_page=current_page)
        answers = answers[pages['range']]
        context_data.update(question=question,
                            answers=answers,
                            pages=pages,
                            question_owner=None,
                            correct_answer=correct_answer)
        if question:
            context_data.update(question_owner=question.author)
        return context_data

    def form_valid(self, form):
        response = super().form_valid(form)
        user: AbstractUser = self.request.user
        answer_text = form.cleaned_data.get("text")
        answer = Answer(text=answer_text, author=user,
                        question_id=self.kwargs['pk'])
        answer.save()
        return response


class VoteView(QuestionDetailView):
    template_name = "qna/question_detail.html"

    def get_success_url(self):
        pk = int(self.request.GET['q'])
        path = reverse("qna:question", kwargs={"pk": pk})
        return path

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        query_params = self.request.GET
        user: AbstractUser = self.request.user
        q_pk = int(query_params['q'])
        a_pk = query_params.get("a")
        is_correct = query_params.get("is_correct")
        is_correct = json.loads(is_correct) if isinstance(is_correct, str) else None
        question = answer = None
        if a_pk and isinstance(is_correct, bool):
            # Помечаем правильный ответ
            a_pk = int(a_pk)
            answer = Answer.objects.filter(pk=a_pk).first()
            answer.is_correct = is_correct
            answer.save()
        else:
            if a_pk:
                # Голосование за ответ
                a_pk = int(a_pk)
                answer = Answer.objects.filter(pk=a_pk).first()
            else:
                # Голосование за вопрос
                question = Question.objects.filter(pk=q_pk).first()
            up = query_params.get("up")
            up = json.loads(up) if isinstance(up, str) and up else None
            try:
                self._up_or_down_vote(user=user, question=question, answer=answer, up=up)
            except:
                pass
        path = reverse("qna:question", kwargs={"pk": q_pk})
        return HttpResponseRedirect(path)

    def _up_or_down_vote(self,
                         user: AbstractUser,
                         question: Question | None = None,
                         answer: Answer | None = None,
                         up: bool = None):
        """Голосование за или против"""
        if up is True:
            vote = Vote(user=user, question=question, answer=answer)
            vote.save()
        elif up is False:
            vote = Vote.objects.filter(user=user)
            if answer:
                vote = vote.filter(answer=answer)
            elif question:
                vote = vote.filter(question=question)
            vote = vote.first()
            vote.delete()
