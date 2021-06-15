import logging
import typing
from abc import ABC
from datetime import timedelta
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
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
        auth = AuthJWT()

        try:
            decoded_token = auth.get_raw_jwt(key)
            request.user = User.objects.get(username=decoded_token["sub"])
            return decoded_token
        except Exception as e:
            logger.warning("fail to refresh JWT token: %s", e)
            return None


class JWTAuthBearer(HttpBearer):
    """Verify JWT token"""

    def authenticate(self, request, token):
        auth = AuthJWT()
        decoded_token = None
        try:
            decoded_token = auth.get_raw_jwt(token)
            request.user = User.objects.get(username=decoded_token["sub"])
        except User.DoesNotExist:
            logger.warning("User doesn't exist: %s", decoded_token)
        except JWTDecodeError as e:
            logger.warning("Fail to verify the token: %s", e.message)
        except ValueError as e:
            logger.warning("Malformed token: %s", e)

        return decoded_token


class JWTAuthUserBearer(JWTAuthBearer):
    """Verify JWT token and make sure the user is active"""

    def authenticate(self, request, token):
        decoded_token = super().authenticate(request, token)
        if request.user.is_active:
            return decoded_token
        return None


@router.post("/token", response=schemas.JWTToken)
def create_jwt_token(request, payload: schemas.JWTTokenCreation):
    try:
        user = User.objects.get(username=payload.username)
        if not user.is_active:
            raise User.DoesNotExist()
        if not user.check_password(payload.password):
            raise User.DoesNotExist()

        return JWTLogin().login(user)
    except User.DoesNotExist:
        raise errors.HttpError(400, "Invalid username or password")


@router.post("/token/refresh", auth=RefreshTokenCookieAuth(), response=schemas.JWTToken)
def refresh_jwt_token(request):
    return JWTLogin().login(request.user, refresh_cookie=False)


class JWTLogin:
    def __init__(self):
        self.auth = AuthJWT()

    def login(
        self,
        user,
        user_claims: typing.Optional[typing.Dict] = None,
        refresh_cookie: bool = True,
    ) -> JsonResponse:
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        if user_claims is None:
            user_claims = {}
        resp_payload = schemas.JWTToken(
            access=self.auth.create_access_token(
                subject=user.username, user_claims=user_claims
            ),
        ).dict()
        # workaround to set Cookie in the response, see: https://github.com/vitalik/django-ninja/issues/117
        resp = JsonResponse(resp_payload)
        if refresh_cookie:
            resp.set_cookie(
                RefreshTokenCookieAuth.param_name,
                self.auth.create_refresh_token(subject=user.username),
                httponly=True,
                domain=settings.SHARED_TW_SETTINGS["DOMAIN"],
            )
        return resp
