from http import HTTPStatus
from typing import Type
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.test import TestCase
from django.urls import reverse

from qna.models import Question, Tag, Answer, Vote

UserModel: Type[AbstractUser] = get_user_model()


class VoteViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = "user_testing"
        cls.password = "password!23"
        cls.user: AbstractUser = UserModel.objects.create_user(
            username=cls.username,
            password=cls.password
        )
        cls.tag_1_text = "tag123"
        cls.tag_2_text = "tag456"
        tag_1 = Tag(text=cls.tag_1_text)
        tag_2 = Tag(text=cls.tag_2_text)
        tag_1.save(), tag_2.save()
        cls.title = "Title1366"
        cls.text = "Text777"
        cls.question = Question.objects.create(title=cls.title,
                                               text=cls.text,
                                               author=cls.user)
        cls.question.tag.set([tag_1, tag_2])
        cls.answer = Answer(author=cls.user,
                            question=cls.question,
                            text=uuid4())
        cls.answer.save()
        # Создадим пачку пользователей
        cls.users = [UserModel.objects.create_user(username=str(uuid4()),
                                                   password=str(uuid4()))
                     for _ in range(30)]

    def setUp(self):
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

    def test_valid_votes_count(self):
        question_votes_number = 12
        answer_votes_number = 30

        with transaction.atomic():
            for i in range(question_votes_number):
                user = self.users[i]
                vote = Vote(user=user, question=self.question)
                vote.save()
            for i in range(answer_votes_number):
                user = self.users[i]
                vote = Vote(user=user, answer=self.answer)
                vote.save()
        question_votes_count = self.question.vote_set.count()
        answer_votes_count = self.answer.vote_set.count()
        self.assertEqual(question_votes_number, question_votes_count)
        self.assertEqual(answer_votes_number, answer_votes_count)

