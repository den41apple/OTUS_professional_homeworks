from http import HTTPStatus
from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase
from django.urls import reverse

UserModel: Type[AbstractUser] = get_user_model()


class AskQuestionViewTestCase(TestCase):

    def setUp(self):
        self.username = "user_testing"
        self.password = "password!23"
        self.user: AbstractUser = UserModel.objects.create_user(
            username=self.username,
            password=self.password
        )

    def test_valid_template(self):
        self.client.login(
            username=self.username,
            password=self.password
        )
        url = reverse("qna:ask")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "qna/ask.html")

    def test_no_access(self):
        url = reverse("qna:ask")
        response = self.client.get(url)
        self.assertEqual(response.status_code,
                         HTTPStatus.FOUND)

    def test_valid_redirect_when_no_access(self):
        url = reverse("qna:ask")
        response = self.client.get(url)
        expected_url = reverse("site_auth:login") + f"?next={url}"
        self.assertRedirects(response, expected_url)

    def test_status_ok(self):
        self.client.login(
            username=self.username,
            password=self.password
        )
        url = reverse("qna:ask")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
