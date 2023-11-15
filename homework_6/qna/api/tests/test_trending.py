from typing import Type
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Count
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from qna.models import Question

UserModel: Type[AbstractUser] = get_user_model()


class TrendingTests(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим пользователя
        cls.username = "test_user"
        cls.password = "test_password!123"
        cls.user = UserModel.objects.create_user(
            username=cls.username,
            password=cls.password
        )
        cls.count_questions = 50
        # Создадим вопросы
        with transaction.atomic():
            for i in range(cls.count_questions):
                question = Question(author=cls.user,
                                    title=str(uuid4()),
                                    text=str(uuid4()))
                question.save()

    def setUp(self):
        # Получим токен
        url = reverse("token_obtain_pair")
        response = self.client.post(url, data={"username": self.username,
                                               "password": self.password})
        self.token = response.data["access"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_valid_authorized_request(self):
        url = reverse("api_trending-list")
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_restricted_access(self):
        url = reverse("api_trending-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_count_elements(self):
        url = reverse("api_trending-list")
        response = self.client.get(url, headers=self.headers)
        questions = response.data
        self.assertEqual(len(questions), 5)

    def test_valid_queryset(self):
        url = reverse("api_trending-list")
        response = self.client.get(url, headers=self.headers)
        queryset = (Question
                    .objects
                    .prefetch_related("vote_set")
                    .annotate(votes_count=Count("vote"))
                    .order_by("-votes_count")
                    .all())[:5]
        self.assertQuerySetEqual(qs=queryset,
                                 values=(el['id'] for el in response.data),
                                 transform=lambda el: el.pk)
