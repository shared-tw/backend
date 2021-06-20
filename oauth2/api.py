import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse
from ninja import Router
from requests_oauthlib import OAuth2Session

from authenticator.api import Authenticator
from authenticator.schemas import JWTToken
from oauth2 import models

LINE_CLIENT_ID = settings.SHARED_TW_SETTINGS["line_client_id"]
LINE_CLIENT_SECRET = settings.SHARED_TW_SETTINGS["line_client_secret"]

logger = logging.getLogger(__name__)
authorization_base_url = "https://access.line.me/oauth2/v2.1/authorize"
token_url = "https://api.line.me/oauth2/v2.1/token"
router = Router(tags=["OAuth"])
User = get_user_model()


@router.get("/line/login", response=JWTToken)
def oauth_line_login(request, next: str):
    redirect_uri = request.build_absolute_uri(reverse("api-0.1.0:line-login-callback"))
    line = OAuth2Session(
        LINE_CLIENT_ID,
        scope=["profile"],
        redirect_uri=redirect_uri,
    )
    authorization_url, state = line.authorization_url(
        authorization_base_url, ui_locales="zh-TW,en"
    )

    resp = HttpResponseRedirect(authorization_url)
    resp.set_cookie("line_oauth_state", state)
    resp.set_cookie("next", next)

    return resp


@router.get("/line/callback", url_name="line-login-callback", include_in_schema=False)
def get(request, code: str, state: str):
    site = get_current_site(request)
    try:
        if request.COOKIES["line_oauth_state"] != state:
            raise ValueError("line_oauth_state != state!?")

        line = OAuth2Session(
            LINE_CLIENT_ID,
            state=state,
            redirect_uri=request.build_absolute_uri(
                reverse("api-0.1.0:line-login-callback")
            ),
        )
        line.fetch_token(
            token_url,
            client_secret=LINE_CLIENT_SECRET,
            authorization_response=request.build_absolute_uri(),
        )
        url = f'{request.scheme}://{site.domain}{request.COOKIES["next"]}'

        profile = line.get("https://api.line.me/v2/profile").json()
        user, created = User.objects.get_or_create(username=profile["userId"])
        if created:
            user.last_name = profile["displayName"]
            user.is_active = False
            user.save()
            models.Profile.objects.create(
                user=user,
                line_id=profile["userId"],
                display_name=profile["displayName"],
                picture_url=profile["pictureUrl"],
            )

        authenticator = Authenticator()
        access_token, refresh_token = authenticator.login(user)
        # FIXME: remove
        print("oauth:", access_token)
        return authenticator.generate_http_response(
            request,
            HttpResponseRedirect,
            refresh_token,
            resp_kwargs=dict(redirect_to=url, content=""),
            unpack_resp_kwargs=True,
        )

    except Exception as e:
        logger.warning("Line auth callback failed: %s", e)
        return HttpResponseBadRequest("Invalid request")
