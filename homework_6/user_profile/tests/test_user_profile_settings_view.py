from http import HTTPStatus
from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase
from django.urls import reverse

UserModel: Type[AbstractUser] = get_user_model()


class UserProfileSettingsViewTestCase(TestCase):

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
        url = reverse("user_profile:settings")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "user_profile/settings.html")

    def test_no_access(self):
        self.client.logout()
        url = reverse("user_profile:settings")
        response = self.client.get(url)
        self.assertEqual(response.status_code,
                         HTTPStatus.FOUND)

    def test_valid_redirect(self):
        self.client.logout()
        url = reverse("user_profile:settings")
        response = self.client.get(url)
        login_url = reverse("site_auth:login")
        redirect_url = login_url + f"?next={url}"
        self.assertRedirects(response, redirect_url)
