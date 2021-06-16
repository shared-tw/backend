import logging
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse
from django.views.generic.base import RedirectView, View
from requests_oauthlib import OAuth2Session

from authenticator.api import JWTLogin

from . import models

authorization_base_url = "https://access.line.me/oauth2/v2.1/authorize"
token_url = "https://api.line.me/oauth2/v2.1/token"
logger = logging.getLogger(__name__)

LINE_CLIENT_ID = settings.SHARED_TW_SETTINGS["LINE_CLIENT_ID"]
LINE_CLIENT_SECRET = settings.SHARED_TW_SETTINGS["LINE_CLIENT_SECRET"]

User = get_user_model()


class LineAuthView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        redirect_uri = self.request.build_absolute_uri(reverse("line-login-callback"))
        # FIXME: scheme detection
        # redirect_uri = redirect_uri.replace("http", "https")
        line = OAuth2Session(
            LINE_CLIENT_ID,
            scope=["profile"],
            redirect_uri=redirect_uri,
        )
        authorization_url, state = line.authorization_url(
            authorization_base_url, ui_locales="zh-TW,en"
        )

        self.request.session["line_oauth_state"] = state
        next_url = urlparse(self.request.GET.get("next", "")).path
        if not next_url:
            return None

        self.request.session["next"] = next_url
        return authorization_url


class LineAuthCallbackView(View):
    def get(self, request, *args, **kwargs):
        try:
            line = OAuth2Session(
                LINE_CLIENT_ID,
                state=self.request.session["line_oauth_state"],
                redirect_uri=self.request.build_absolute_uri(
                    reverse("line-login-callback")
                ),
            )
            line.fetch_token(
                token_url,
                client_secret=LINE_CLIENT_SECRET,
                authorization_response=self.request.build_absolute_uri(),
            )
            profile = line.get("https://api.line.me//v2/profile").json()
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
            _, refresh_token = JWTLogin().login(user)
            url = f'{request.scheme}://{settings.SHARED_TW_SETTINGS["DOMAIN"]}{request.session["next"]}'
            resp = HttpResponseRedirect(url)
            return JWTLogin.set_refresh_cookie(resp, refresh_token)

        except Exception as e:
            logger.warning("Line auth callback failed: %s", e)
            return HttpResponseBadRequest("Invalid request")
