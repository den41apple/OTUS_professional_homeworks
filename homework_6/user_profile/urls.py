from django.urls import path

from user_profile.views import UserProfileSettingsView

app_name = "user_profile"

urlpatterns = [
    path("settings/", UserProfileSettingsView.as_view(), name="settings")
]
