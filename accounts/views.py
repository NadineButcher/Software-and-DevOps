# accounts/views.py

from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView

from django_ratelimit.decorators import ratelimit

from .forms import CustomUserCreationForm

# ============================================================
# SIGN UP
# ============================================================

@method_decorator(
    ratelimit(
        key="ip",
        rate="5/m",
        method="POST",
        block=True,
    ),
    name="post",
)
class SignUpView(CreateView):

    form_class = CustomUserCreationForm

    template_name = "registration/signup.html"

    success_url = reverse_lazy("passkeys:register_page")

def form_valid(self, form):
    response = super().form_valid(form)

    # Automatically log the newly-created user in.
    login(
        self.request,
        self.object,
        backend="django.contrib.auth.backends.ModelBackend",
    )

    return response


# ============================================================
# COMBINED LOGIN
# ============================================================

def login_combined(request):

    form = AuthenticationForm(
        request,
        data=request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        login(
            request,
            form.get_user()
        )

        return redirect("home")

    return render(
        request,
        "login_combined.html",
        {
            "form": form
        }
    )


# ============================================================
# PASSWORDLESS LOGIN VIA SECURITY KEY
# ============================================================

def login_with_key(request):

    user = getattr(
        request,
        "webauthn_user",
        None
    )

    if user:

        login(
            request,
            user
        )

        return redirect("home")

    return redirect("login_combined")
