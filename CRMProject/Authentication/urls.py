from django.urls import path
from .views import LoginView,LogoutView
from .views import ForgotPasswordView, ResetPasswordView


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/<uuid:token>/", ResetPasswordView.as_view()),
]