# accounts/urls.py
from django.urls import path
from .views import SignUpView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
    #path("logout/<str:next_page>/", auth_views.LogoutView.as_view(), name="logout_no_slash"),

