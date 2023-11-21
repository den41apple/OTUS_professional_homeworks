from typing import Type
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.db.models import Count, Q
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from qna.models import Question

UserModel: Type[AbstractUser] = get_user_model()


class SearchTests(APITestCase):

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
            question = Question(author=cls.user,
                                title="How to turn on computer?",
                                text="I have a problem")
            question.save()

    def setUp(self):
        # Получим токен
        url = reverse("token_obtain_pair")
        response = self.client.post(url, data={"username": self.username,
                                               "password": self.password})
        self.token = response.data["access"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_valid_authorized_request(self):
        url = reverse("api_search-list")
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_restricted_access(self):
        url = reverse("api_search-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_count_elements(self):
        url = reverse("api_search-list")
        url += '?q=computer'
        response = self.client.get(url, headers=self.headers)
        questions = response.data['results']
        count_questions = response.data['count']
        self.assertEqual(count_questions, 1)
        self.assertEqual(len(questions), 1)

    def test_valid_data(self):
        url = reverse("api_search-list")
        search_text = "computer"
        url += f'?q={search_text}'
        response = self.client.get(url, headers=self.headers)
        queryset = (Question.objects
                    .select_related("author")
                    .select_related("author__profile")
                    .prefetch_related("answer_set")
                    .prefetch_related("vote_set")
                    .prefetch_related("tag")
                    .annotate(votes_count=Count("vote"))
                    .order_by("-votes_count", "-created_at")
                    .filter(Q(title__icontains=search_text)
                            | Q(text__icontains=search_text)
                            | Q(answer__text__icontains=search_text))
                    .all())
        self.assertQuerySetEqual(qs=queryset,
                                 values=(el['id'] for el in response.data["results"]),
                                 transform=lambda el: el.pk)
