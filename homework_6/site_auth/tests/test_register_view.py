from http import HTTPStatus
from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.test import TestCase
from django.urls import reverse

UserModel: Type[AbstractUser] = get_user_model()


class RegisterViewTestCase(TestCase):

    def test_valid_template(self):
        url = reverse("site_auth:signup")
        response = self.client.get(url)
        self.assertTemplateUsed(response, "site_auth/register.html")

    def test_user_create_success(self):
        url = reverse("site_auth:signup")
        username = "user123"
        response = self.client.post(url, {"username": username,
                                          "email": "example@mail.ru",
                                          "password1": "Pass!134",
                                          "password2": "Pass!134"})
        users = UserModel.objects.all()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user.username, username)

    def test_form_errors(self):
        url = reverse("site_auth:signup")
        response = self.client.post(url, {"username": "user123",
                                          "email": "examplemail.ru",
                                          "password1": "1",
                                          "password2": "1"})
        form = response.context_data["form"]
        self.assertFormError(form, "email", ["Enter a valid email address."])
