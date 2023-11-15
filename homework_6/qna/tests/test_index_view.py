from http import HTTPStatus
from typing import Type
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.test import TestCase
from django.urls import reverse

from qna.models import Question

UserModel: Type[AbstractUser] = get_user_model()


class IndexViewTestCase(TestCase):

    def setUp(self):
        self.username = "user_testing"
        self.password = "password!23"
        self.user: AbstractUser = UserModel.objects.create_user(
            username=self.username,
            password=self.password
        )

    def test_status_ok(self):
        url = reverse("qna:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_valid_template(self):
        url = reverse("qna:index")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "qna/index.html")

    def test_valid_pagination_in_html_exists(self):
        with transaction.atomic():
            # Создадим вопросы
            for _ in range(65):
                question = Question(author=self.user,
                                    title=uuid4(),
                                    text=uuid4())
                question.save()
        url = reverse("qna:index")
        response = self.client.get(url)
        self.assertInHTML('<a class="page-link" href="#" tabindex="-1" aria-disabled="true">Previous</a>',
                          response.content.decode(), count=1)
        # 6 кнопок должно быть
        self.assertContains(response, '<a class="page-link', count=6)

    def test_question_titles_exists(self):
        titles = []
        # Создадим вопросы, не более 20-и
        with transaction.atomic():
            for i in range(20):
                title = uuid4()
                question = Question(author=self.user,
                                    title=title,
                                    text=uuid4())
                titles.append(title)
                question.save()
        url = reverse("qna:index")
        response = self.client.get(url)
        for title in titles:
            self.assertContains(response, title)

    def test_valid_queryset(self):
        with transaction.atomic():
            # Создадим вопросы, не более 20-и
            for i in range(20):
                question = Question(author=self.user,
                                    title=uuid4(),
                                    text=uuid4())
                question.save()
        url = reverse("qna:index")
        response = self.client.get(url)
        queryset = (Question.objects
                    .order_by("-created_at")  # По умолчанию created_at DESC
                    .only("id")
                    .all())
        self.assertQuerySetEqual(qs=queryset,
                                 values=(el.pk for el in response.context_data["questions"]),
                                 transform=lambda el: el.pk)
