from functools import wraps

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from hashids import Hashids
from ninja import errors

_hashids = Hashids(
    settings.AUTHENTICATOR["hash_id_secret"],
    min_length=settings.AUTHENTICATOR["min_length"],
)


def encode_id(id: int) -> str:
    return _hashids.encode(id)


def decode_id(data: str) -> int:
    return _hashids.decode(data)[0]


def is_verified_email_or_403(view_func):
    # Workaround to ensure the user's email is verified.
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_active:
            raise errors.HttpError(403, "Please verify your Email address.")
        return view_func(*args, **kwargs)

    return wraps(view_func)(wrapped_view)


def send_verification_email(request, user):
    site = get_current_site(request)

    token = default_token_generator.make_token(user)
    path = settings.AUTHENTICATOR["verification_email_url"].format(
        uid=encode_id(user.id), token=token
    )
    mail_title = "Shared TW - Email 驗證信"
    context = {
        "proto": "https" if request.is_secure() else "http",
        "domain": site.domain,
        "path": path,
    }
    html = render_to_string("email/verification_email.html", context).strip()
    text = render_to_string("email/verification_email.txt", context).strip()

    msg = EmailMultiAlternatives(mail_title, text, to=[user.email])
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)
