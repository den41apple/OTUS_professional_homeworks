from http import HTTPStatus
from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase
from django.urls import reverse

UserModel: Type[AbstractUser] = get_user_model()


class LogoutViewTestCase(TestCase):

    def setUp(self):
        self.username = "user_testing"
        self.password = "password!23"
        self.user: AbstractUser = UserModel.objects.create_user(
            username=self.username,
            password=self.password
        )
        self.client.login(username=self.username,
                          password=self.password)

    def test_user_logout(self):
        response = self.client.get(reverse("qna:index"))
        user: UserModel = response.context["user"]
        self.assertFalse(user.is_anonymous)
        self.client.get(reverse("site_auth:logout"))
        response = self.client.get(reverse("qna:index"))
        user: UserModel = response.context["user"]
        self.assertTrue(user.is_anonymous)

    def test_valid_redirect(self):
        response = self.client.get(reverse("qna:index"))
        user: UserModel = response.context["user"]
        self.assertFalse(user.is_anonymous)
        response = self.client.get(reverse("site_auth:logout"))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse("qna:index"))
