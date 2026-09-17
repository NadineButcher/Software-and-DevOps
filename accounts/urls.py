# accounts/urls.py
from django.urls import path
from .views import SignUpView, login_combined
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", login_combined, name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]