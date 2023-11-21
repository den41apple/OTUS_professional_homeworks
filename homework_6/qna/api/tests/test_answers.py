from typing import Type
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from qna.models import Question, Answer

UserModel: Type[AbstractUser] = get_user_model()


class AnswerTests(APITestCase):

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
        cls.count_answers = 50
        # Создадим вопрос и ответы
        with transaction.atomic():
            cls.question = Question(author=cls.user,
                                    title=str(uuid4()),
                                    text=str(uuid4()))
            cls.question.save()
            for i in range(cls.count_answers):
                answer = Answer(author=cls.user,
                                question=cls.question,
                                text=str(uuid4()))
                answer.save()

    def setUp(self):
        # Получим токен
        url = reverse("token_obtain_pair")
        response = self.client.post(url, data={"username": self.username,
                                               "password": self.password})
        self.token = response.data["access"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_valid_authorized_request(self):
        url = reverse("api_answers-list")
        question_id = self.question.id
        url += f'?question_id={question_id}'
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_restricted_access(self):
        url = reverse("api_answers-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_parameter(self):
        url = reverse("api_answers-list")
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("error", response.data)

    def test_count_elements(self):
        url = reverse("api_answers-list")
        question_id = self.question.id
        url += f'?page_size=10&question_id={question_id}'
        response = self.client.get(url, headers=self.headers)
        questions = response.data['results']
        count_questions = response.data['count']
        self.assertEqual(self.count_answers, count_questions)
        self.assertEqual(len(questions), 10)

    def test_valid_queryset(self):
        url = reverse("api_answers-list")
        question_id = self.question.id
        url += f'?page_size=10&question_id={question_id}'
        response = self.client.get(url, headers=self.headers)
        queryset = (Answer
                    .objects
                    .filter(question_id=self.question.id)
                    .order_by("-created_at")
                    .all())[:10]
        self.assertQuerySetEqual(qs=queryset,
                                 values=(el['id'] for el in response.data["results"]),
                                 transform=lambda el: el.pk)
