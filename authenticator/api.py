import logging
import typing
from abc import ABC
from datetime import timedelta
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.http.response import JsonResponse
from django.utils import timezone
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import JWTDecodeError
from ninja import Router, Schema, errors
from ninja.security import HttpBearer
from ninja.security.apikey import APIKeyBase

from . import schemas

logger = logging.getLogger(__name__)

User = get_user_model()
router = Router(tags=["Authentication"])


class Settings(Schema):
    authjwt_secret_key: str = settings.SECRET_KEY
    authjwt_access_token_expires: int = timedelta(hours=1)


@AuthJWT.load_config
def get_config():
    return Settings()


class RefreshTokenCookieAuth(APIKeyBase, ABC):
    """Check is refresh token exists in the Cookies"""

    # We don't inherit APIKeyCookie
    openapi_in: str = "cookie"
    param_name = "refresh-token"

    def _get_key(self, request: HttpRequest) -> Optional[str]:
        return request.COOKIES.get(self.param_name)

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        user, decoded_token = JWTLogin().authenticate(key)
        if user:
            request.user = user
        else:
            return None
        return decoded_token


class JWTAuthBearer(HttpBearer):
    """Verify JWT token"""

    def authenticate(self, request, token):
        user, decoded_token = JWTLogin().authenticate(token, is_active=None)
        if user:
            request.user = user
        return decoded_token


class JWTAuthUserBearer(HttpBearer):
    """Verify JWT token and make sure the user is active"""

    def authenticate(self, request, token):
        user, decoded_token = JWTLogin().authenticate(token)
        if user:
            request.user = user
        return decoded_token


@router.post("/token", response=schemas.JWTToken)
def create_jwt_token(request, payload: schemas.JWTTokenCreation):
    try:
        user = User.objects.get(username=payload.username, is_active=True)
        if not user.check_password(payload.password):
            raise User.DoesNotExist()

        access_token, refresh_token = JWTLogin().login(user)
        resp = JsonResponse(schemas.JWTToken(access=access_token).dict())
        return JWTLogin.set_refresh_cookie(resp, refresh_token)
    except User.DoesNotExist:
        raise errors.HttpError(400, "Invalid username or password")


@router.post("/token/refresh", auth=RefreshTokenCookieAuth(), response=schemas.JWTToken)
def refresh_jwt_token(request):
    access_token, refresh_token = JWTLogin().login(request.user)

    # workaround to set Cookie in the response, see: https://github.com/vitalik/django-ninja/issues/117
    resp = JsonResponse(schemas.JWTToken(access=access_token).dict())
    return JWTLogin.set_refresh_cookie(resp, refresh_token)


class JWTLogin:
    def __init__(self):
        self.auth = AuthJWT()

    def login(
        self,
        user,
        user_claims: typing.Optional[typing.Dict] = None,
    ) -> typing.Tuple[str, str]:
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        if user_claims is None:
            user_claims = {}

        return self.auth.create_access_token(
            subject=user.username, user_claims=user_claims
        ), self.auth.create_refresh_token(subject=user.username)

    def authenticate(self, token, is_active: typing.Optional[bool] = None):
        user = None
        decoded_token = None
        kwargs = {}
        if is_active is not None:
            kwargs["is_active"] = is_active

        try:
            decoded_token = self.auth.get_raw_jwt(token)
            user = User.objects.get(username=decoded_token["sub"], **kwargs)
        except User.DoesNotExist:
            logger.warning("User doesn't exist: %s", decoded_token)
        except JWTDecodeError as e:
            logger.warning("Fail to verify the token: %s", e.message)
        except ValueError as e:
            logger.warning("Malformed token: %s", e)

        return user, decoded_token

    @classmethod
    def set_refresh_cookie(cls, resp: HttpResponse, refresh_token: str) -> HttpResponse:
        resp.set_cookie(
            RefreshTokenCookieAuth.param_name,
            refresh_token,
            httponly=True,
            domain=settings.SHARED_TW_SETTINGS["DOMAIN"],
            samesite="Strict",
            max_age=timedelta(days=7).total_seconds(),
        )
        return resp
