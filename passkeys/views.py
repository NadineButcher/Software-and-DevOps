# passkeys/views.py

import base64
import json

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST

from django_ratelimit.decorators import ratelimit

from webauthn import (
    generate_registration_options,
    generate_authentication_options,
    verify_registration_response,
    verify_authentication_response,
    options_to_json,
)

from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
)


# ============================================================
# WebAuthn configuration
# ============================================================

RP_ID = "localhost"
RP_NAME = "My Django Site"
ORIGIN = "http://localhost:8000"


# ============================================================
# Helpers
# ============================================================

def base64url_decode(value):
    """
    Decode a Base64URL string to bytes.
    """

    if isinstance(value, bytes):
        return value

    padding = "=" * (-len(value) % 4)

    return base64.urlsafe_b64decode(
        value + padding
    )


def base64url_encode(value):
    """
    Encode bytes as a WebAuthn-compatible Base64URL string.
    """

    return (
        base64.urlsafe_b64encode(value)
        .rstrip(b"=")
        .decode("ascii")
    )


def get_credentials(user):
    """
    Return the user's stored WebAuthn credentials.
    """

    return user.webauthn_credentials or []


# ============================================================
# PASSKEY REGISTRATION PAGE
# ============================================================

@login_required
def register_page(request):
    """
    Display the page where the logged-in user can
    register a passkey.
    """

    return render(
        request,
        "passkeys/register.html"
    )


# ============================================================
# PASSKEY REGISTRATION - START
# ============================================================

@login_required
def register_start(request):
    """
    Generate WebAuthn registration options.

    The user must already be logged in.
    """

    credentials = get_credentials(
        request.user
    )

    exclude_credentials = []

    for credential in credentials:

        credential_id = credential.get("id")

        if credential_id:

            exclude_credentials.append(
                PublicKeyCredentialDescriptor(
                    id=base64url_decode(
                        credential_id
                    )
                )
            )

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,

        user_name=request.user.username,

        user_id=str(
            request.user.id
        ).encode("utf-8"),

        user_display_name=(
            request.user.get_full_name()
            or request.user.username
        ),

        exclude_credentials=(
            exclude_credentials
        ),
    )

    # Store challenge in the session.
    request.session[
        "webauthn_reg_challenge"
    ] = base64url_encode(
        options.challenge
    )

    return JsonResponse(
        json.loads(
            options_to_json(options)
        )
    )


# ============================================================
# PASSKEY REGISTRATION - FINISH
# ============================================================

@login_required
def register_finish(request):
    """
    Verify and store the newly-created passkey.
    """

    try:

        data = json.loads(
            request.body
        )

        challenge_b64 = (
            request.session.get(
                "webauthn_reg_challenge"
            )
        )

        if not challenge_b64:

            return JsonResponse(
                {
                    "error":
                        "Missing registration challenge."
                },
                status=400,
            )

        expected_challenge = (
            base64url_decode(
                challenge_b64
            )
        )

        verification = (
            verify_registration_response(
                credential=data,

                expected_challenge=(
                    expected_challenge
                ),

                expected_rp_id=(
                    RP_ID
                ),

                expected_origin=(
                    ORIGIN
                ),
            )
        )

        # Get current credentials.
        credentials = get_credentials(
            request.user
        )

        # Create stored credential.
        credential = {
            "id": base64url_encode(
                verification.credential_id
            ),

            "public_key": base64url_encode(
                verification.credential_public_key
            ),

            "sign_count":
                verification.sign_count,
        }

        credentials.append(
            credential
        )

        request.user.webauthn_credentials = (
            credentials
        )

        request.user.save(
            update_fields=[
                "webauthn_credentials"
            ]
        )

        # Consume challenge.
        request.session.pop(
            "webauthn_reg_challenge",
            None
        )

        return JsonResponse(
            {
                "status": "ok",

                "message":
                    "Passkey registered successfully.",
            }
        )

    except Exception as e:

        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )


# ============================================================
# PASSKEY LOGIN - START
# ============================================================

@ratelimit(
    key="ip",
    rate="10/m",
    method="GET",
    block=True,
)

def auth_start(request):
    
    """
    Generate WebAuthn authentication options.
    The user does NOT need to be logged in.
    """

    options = generate_authentication_options(
        rp_id=RP_ID,
    )

    request.session[
        "webauthn_auth_challenge"
    ] = base64url_encode(
        options.challenge
    )

    return JsonResponse(
        json.loads(
            options_to_json(options)
        )
    )


# ============================================================
# PASSKEY LOGIN - FINISH
# ============================================================

@ratelimit(
    key="ip",
    rate="5/m",
    method="POST",
    block=True,
)
def auth_finish(request):
    """
    Verify the passkey and log the user into Django.
    """
    try:

        data = json.loads(
            request.body
        )

        challenge_b64 = (
            request.session.get(
                "webauthn_auth_challenge"
            )
        )

        if not challenge_b64:

            return JsonResponse(
                {
                    "error":
                        "Missing authentication challenge."
                },
                status=400,
            )

        expected_challenge = (
            base64url_decode(
                challenge_b64
            )
        )

        credential_id = data.get(
            "rawId"
        )

        if not credential_id:

            return JsonResponse(
                {
                    "error":
                        "Missing credential ID."
                },
                status=400,
            )

        # ----------------------------------------------------
        # Find the user who owns this passkey
        # ----------------------------------------------------

        User = get_user_model()

        matched_user = None
        stored_credential = None
        matched_credentials = None

        for user in User.objects.all():

            user_credentials = (
                getattr(
                    user,
                    "webauthn_credentials",
                    None,
                )
                or []
            )

            for credential in user_credentials:

                if (
                    credential.get("id")
                    == credential_id
                ):

                    matched_user = user

                    stored_credential = (
                        credential
                    )

                    matched_credentials = (
                        user_credentials
                    )

                    break

            if matched_user is not None:
                break

        if matched_user is None:

            return JsonResponse(
                {
                    "error":
                        "Passkey not recognised."
                },
                status=400,
            )

        # ----------------------------------------------------
        # Retrieve stored public key
        # ----------------------------------------------------

        try:

            public_key = (
                base64url_decode(
                    stored_credential[
                        "public_key"
                    ]
                )
            )

            current_sign_count = int(
                stored_credential.get(
                    "sign_count",
                    0,
                )
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as e:

            return JsonResponse(
                {
                    "error":
                        f"Invalid stored passkey: {e}"
                },
                status=400,
            )

        # ----------------------------------------------------
        # Verify WebAuthn assertion
        # ----------------------------------------------------

        verification = (
            verify_authentication_response(
                credential=data,

                expected_challenge=(
                    expected_challenge
                ),

                expected_rp_id=(
                    RP_ID
                ),

                expected_origin=(
                    ORIGIN
                ),

                credential_public_key=(
                    public_key
                ),

                credential_current_sign_count=(
                    current_sign_count
                ),
            )
        )

        # ----------------------------------------------------
        # Update signature counter
        # ----------------------------------------------------

        stored_credential[
            "sign_count"
        ] = verification.new_sign_count

        matched_user.webauthn_credentials = (
            matched_credentials
        )

        matched_user.save(
            update_fields=[
                "webauthn_credentials"
            ]
        )

        # ----------------------------------------------------
        # Log user into Django
        # ----------------------------------------------------

        login(
            request,
            matched_user,
            backend="django.contrib.auth.backends.ModelBackend"
        )

        # ----------------------------------------------------
        # Consume challenge
        # ----------------------------------------------------

        request.session.pop(
            "webauthn_auth_challenge",
            None
        )

        return JsonResponse(
            {
                "status": "ok",

                "message":
                    "Passkey authentication successful.",

                "redirect_url":
                    "/",
            }
        )

    except Exception as e:

        return JsonResponse(
            {
                "error": str(e)
            },
            status=400,
        )

