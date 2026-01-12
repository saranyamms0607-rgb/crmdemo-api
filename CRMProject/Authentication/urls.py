from django.urls import path
from .views import LoginView,LogoutView, ForgotPasswordView, ResetPasswordView, UserDropdownView


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("userlist/", UserDropdownView.as_view(), name="userlist"),


    path("forgot-password/", ForgotPasswordView.as_view()),
    path("reset-password/<uuid:token>/", ResetPasswordView.as_view()),
]