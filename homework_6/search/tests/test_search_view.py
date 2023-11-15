from http import HTTPStatus
from typing import Type
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.test import TestCase
from django.urls import reverse

from qna.models import Question, Tag

UserModel: Type[AbstractUser] = get_user_model()


class SearchViewTestCase(TestCase):

    def setUp(self):
        self.username = "user_testing"
        self.password = "password!23"
        self.user: AbstractUser = UserModel.objects.create_user(
            username=self.username,
            password=self.password
        )
        self.client.login(username=self.username,
                          password=self.password)

    def test_valid_template(self):
        url = reverse("search:search")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "search/search.html")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_valid_pagination_in_query(self):
        with transaction.atomic():
            # Создадим одинаковые вопросы
            for _ in range(65):
                question = Question(author=self.user,
                                    title="Title",
                                    text=uuid4())
                question.save()
        url = reverse("search:search")
        url += "?q=Title"
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertInHTML('<a class="page-link" href="#" tabindex="-1" aria-disabled="true">Previous</a>',
                          response.content.decode(), count=1)
        # 6 кнопок должно быть
        self.assertContains(response, '<a class="page-link', count=6)

    def test_valid_pagination_in_tag_query(self):
        with transaction.atomic():
            # Создадим вопросы с одинаковым тэгом
            tag = Tag(text="tag1")
            tag.save()
            for _ in range(65):
                question = Question(author=self.user,
                                    title=uuid4(),
                                    text=uuid4())
                question.save()
                question.tag.set([tag])
        url = reverse("search:search")
        url += "?q=tag:tag1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertInHTML('<a class="page-link" href="#" tabindex="-1" aria-disabled="true">Previous</a>',
                          response.content.decode(), count=1)
        # 6 кнопок должно быть
        self.assertContains(response, '<a class="page-link', count=6)
