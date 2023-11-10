from http import HTTPStatus
from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase
from django.urls import reverse_lazy, reverse

UserModel: Type[AbstractUser] = get_user_model()


class LoginViewTestCase(TestCase):
    login_url = reverse_lazy("site_auth:login")

    def setUp(self):
        self.username = "user_testing"
        self.password = "password!23"
        self.user: AbstractUser = UserModel.objects.create_user(
            username=self.username,
            password=self.password
        )

    def test_login_anonymous(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        user: AbstractUser = response.context["user"]
        self.assertTrue(user.is_anonymous)

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {"username": self.username,
             "password": self.password}
        )
        self.assertRedirects(response, reverse("qna:index"))
        response_logged = self.client.get(reverse("qna:index"))
        self.assertEqual(response_logged.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response_logged, "qna/index.html")
        user: AbstractUser = response_logged.context["user"]
        self.assertFalse(user.is_anonymous)
        self.assertEqual(user.username, self.user.username)
