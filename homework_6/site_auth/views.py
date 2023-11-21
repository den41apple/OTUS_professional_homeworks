from django.contrib.auth import authenticate, login
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.views import (
    LoginView as LoginViewGeneric,
    LogoutView as LogoutViewGeneric,
)
from django.urls import reverse_lazy
from django.views.generic import CreateView

from user_profile.models import Profile
from .forms import UserCreationForm, AuthenticationForm


class RegisterView(CreateView):
    form_class = UserCreationForm
    template_name = "site_auth/register.html"
    success_url = reverse_lazy("qna:index")

    def form_valid(self, form):
        response = super().form_valid(form)
        user: AbstractUser = self.object
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password1")
        avatar = form.files.get("avatar")
        profile: Profile = user.profile
        # Добавим аватар
        profile.avatar = avatar
        profile.save()
        authenticate(self.request, username=username, password=password)
        login(self.request, user=user)
        return response


class LogoutView(LogoutViewGeneric):
    next_page = reverse_lazy("qna:index")


class LoginView(LoginViewGeneric):
    form_class = AuthenticationForm
    template_name = "site_auth/login.html"
    next_page = reverse_lazy("qna:index")
