from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Tag(models.Model):
    text = models.CharField(null=False, blank=False, default="<empty_tag>", max_length=50, unique=True)

    def save(self, *args, **kwargs):
        # Все тэги сохраняем в нижнем регистре
        self.text = self.text.lower()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.text}"


class Question(models.Model):
    title = models.CharField(null=False, blank=False, default="<empty_header>", max_length=100)
    text = models.TextField(null=False, blank=False, default="<empty_text>", max_length=4_096)
    created_at = models.DateTimeField(null=False, blank=False, default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    tag = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return f'{self.author.username}: "{self.title}"'


class Answer(models.Model):
    text = models.TextField(null=False, blank=False, default="<empty_text>", max_length=4_096)
    created_at = models.DateTimeField(null=False, blank=False, default=timezone.now)
    is_correct = models.BooleanField(null=False, blank=False, default=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return f'{self.author.username}: "{self.text}"'


class Vote(models.Model):
    class Meta:
        unique_together = [('user', 'answer'),
                           ('user', 'question')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False, blank=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        text = f"{self.user.username}:"
        if self.question:
            text += f' Q: "{self.question.title}"'
        if self.answer:
            text += f' A: "{self.answer.text}"'
        return text
