import os
from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):

    def upload_to(self, filename: str) -> str:
        directory = "images"
        _uuid = uuid4()
        _filename = f"{self.user.id}_{_uuid}_{filename}"
        path = os.path.join(directory, _filename)
        return path

    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Login")
    avatar = models.ImageField(upload_to=upload_to, verbose_name="Avatar")

    def __str__(self):
        user: User = self.user
        return f"{user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
