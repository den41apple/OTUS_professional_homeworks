from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AbstractUser
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import UserProfileSettingsForm
from .models import Profile


class UserProfileSettingsView(LoginRequiredMixin, FormView):
    form_class = UserProfileSettingsForm
    template_name = "user_profile/settings.html"
    success_url = reverse_lazy("user_profile:settings")

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        # Передадим пользователя в форму
        form_kwargs['user'] = self.request.user
        return form_kwargs


    def form_valid(self, form):
        response = super().form_valid(form)
        user: AbstractUser = self.request.user
        username = form.cleaned_data.get("username")  # Не редактируемое поле
        email = form.cleaned_data.get("email")
        avatar = form.files.get("avatar")
        user.email = email
        if not hasattr(user, "profile"):
            profile = Profile(user=user)
        else:
            profile: Profile = user.profile
        if avatar:
            # Удаляем старый
            if profile.avatar:
                profile.avatar.delete()
            # Устанавливаем новый
            profile.avatar = avatar
        user.save()
        return response
