from http import HTTPStatus
from typing import Type
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase
from django.urls import reverse

from qna.models import Question, Tag, Answer

UserModel: Type[AbstractUser] = get_user_model()


class QuestionDetailViewTestCase(TestCase):

    def setUp(self):
        self.username = "user_testing"
        self.password = "password!23"
        self.user: AbstractUser = UserModel.objects.create_user(
            username=self.username,
            password=self.password
        )
        self.tag_1_text = "tag123"
        self.tag_2_text = "tag456"
        tag_1 = Tag(text=self.tag_1_text)
        tag_2 = Tag(text=self.tag_2_text)
        tag_1.save(), tag_2.save()
        self.title = "Title1366"
        self.text = "Text777"
        self.question = Question.objects.create(title=self.title,
                                                text=self.text,
                                                author=self.user)
        self.question.tag.set([tag_1, tag_2])
        self.client.login(username=self.username,
                          password=self.password)

    def test_valid_template(self):
        url = reverse("qna:question", kwargs={"pk": self.question.pk})
        response = self.client.get(url)
        self.assertTemplateUsed(response, "qna/question_detail.html")

    def test_login_required(self):
        self.client.logout()
        url = reverse("qna:question", kwargs={"pk": self.question.pk})
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        login_path = reverse("site_auth:login")
        redirect_path = login_path + f"?next={url}"
        self.assertRedirects(response, redirect_path)

    def test_question_data_exists(self):
        url = reverse("qna:question", kwargs={"pk": self.question.pk})
        response = self.client.get(url)
        self.assertContains(response, "#" + self.tag_1_text, count=1)
        self.assertContains(response, "#" + self.tag_2_text, count=1)
        self.assertContains(response, self.title, count=2)
        self.assertContains(response, self.text, count=1)

    def test_valid_queryset(self):
        url = reverse("qna:question", kwargs={"pk": self.question.pk})
        response = self.client.get(url)
        queryset = (Question.objects
                    .order_by("-created_at")  # По умолчанию created_at DESC
                    .only("id")
                    .all())
        self.assertQuerySetEqual(qs=queryset,
                                 values=[response.context_data["question"]])

    def test_valid_pagination_in_html_exists(self):
        # Создадим ответы
        for _ in range(65):
            answer = Answer(author=self.user,
                            question=self.question,
                            text=uuid4())
            answer.save()
        url = reverse("qna:question", kwargs={"pk": self.question.pk})
        response = self.client.get(url)
        self.assertInHTML('<a class="page-link" href="#" tabindex="-1" aria-disabled="true">Previous</a>',
                          response.content.decode(), count=1)
        # 5 кнопок должно быть
        self.assertContains(response, '<a class="page-link', count=5)
