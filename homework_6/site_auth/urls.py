from django.urls import path

from .views import RegisterView, LogoutView, LoginView

app_name = "site_auth"

urlpatterns = [
    path("signup/", RegisterView.as_view(), name="signup"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("login/", LoginView.as_view(), name="login"),
]

