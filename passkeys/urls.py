# passkeys/urls.py

from django.urls import path
from . import views


app_name = "passkeys"


urlpatterns = [

    # Passkey registration
    path(
        "register/",
        views.register_page,
        name="register_page",
    ),

    path(
        "register/start/",
        views.register_start,
        name="register_start",
    ),

    path(
        "register/finish/",
        views.register_finish,
        name="register_finish",
    ),

    # Passkey authentication
    path(
        "auth/start/",
        views.auth_start,
        name="auth_start",
    ),

    path(
        "auth/finish/",
        views.auth_finish,
        name="auth_finish",
    ),
]
