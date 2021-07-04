import logging
import typing
from abc import ABC
from datetime import timedelta
from typing import Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from django.http.response import HttpResponseBase, JsonResponse
from django.utils import timezone
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import InvalidHeaderError, JWTDecodeError
from ninja import Router, Schema, errors
from ninja.security import HttpBearer
from ninja.security.apikey import APIKeyBase

from . import schemas, utils

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

    # We don't inherit APIKeyCookie to skip CSRF check for now
    openapi_in: str = "cookie"
    param_name = "refresh-token"

    def _get_key(self, request: HttpRequest) -> Optional[str]:
        return request.COOKIES.get(self.param_name)

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        user, decoded_token = Authenticator().authenticate_by_token(key)
        if not user:
            return None

        request.user = user
        return decoded_token


class JWTAuthBearer(HttpBearer):
    """Verify JWT token"""

    def __init__(self, inactive_user_raise_403: bool = True) -> None:
        super().__init__()
        self.inactive_user_raise_403 = inactive_user_raise_403

    def authenticate(self, request, token):
        user, decoded_token = Authenticator().authenticate_by_token(token)
        if user and not user.is_active and self.inactive_user_raise_403:
            raise errors.HttpError(403, "Please verify your email.")
        elif not user:
            return None

        request.user = user
        return decoded_token


@router.post("/token", response=schemas.JWTToken)
def create_jwt_token(request, payload: schemas.JWTTokenCreation):
    authenticator = Authenticator()

    try:
        user = authenticator.authenticate(payload.username, payload.password)
        if not user.is_active:
            raise errors.HttpError(403, "Please verify your email.")
        access_token, refresh_token = authenticator.login(user)
        kwargs = schemas.JWTToken(access=access_token).dict()
        return authenticator.generate_http_response(
            request, JsonResponse, refresh_token, resp_kwargs=kwargs
        )
    except User.DoesNotExist:
        raise errors.HttpError(400, "Invalid username or password")


@router.post("/token/refresh", auth=RefreshTokenCookieAuth(), response=schemas.JWTToken)
def refresh_jwt_token(request):
    authenticator = Authenticator()
    access_token, refresh_token = authenticator.login(request.user)

    # workaround to set Cookie in the response, see: https://github.com/vitalik/django-ninja/issues/117
    return authenticator.generate_http_response(
        request,
        JsonResponse,
        refresh_token,
        resp_kwargs=schemas.JWTToken(access=access_token).dict(),
    )


@router.get("/verify-email", response=schemas.JWTToken)
def verify_email(request, uid: str, token: str):
    authenticator = Authenticator()
    try:
        access_token, refresh_token = authenticator.verify_email(uid, token)
        kwargs = schemas.JWTToken(access=access_token).dict()
        return authenticator.generate_http_response(
            request, JsonResponse, refresh_token, resp_kwargs=kwargs
        )
    except Exception as e:
        logger.warning("Invalid user or token: %s=%s, err: %s", uid, token, e)
        raise errors.HttpError(401, "Invalid user or token")


class Authenticator:
    def __init__(self):
        self.auth = AuthJWT()

    def login(
        self,
        user,
    ) -> typing.Tuple[str, str]:
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        user_id = utils.encode_id(user.id)
        return self.auth.create_access_token(
            subject=user_id
        ), self.auth.create_refresh_token(subject=user_id)

    def verify_email(self, encoded_id: str, token: str) -> typing.Tuple[str, str]:
        user = User.objects.get(id=utils.decode_id(encoded_id))
        if not default_token_generator.check_token(user, token):
            raise ValueError("Invalid or expired token")
        user.is_active = True
        user.save()
        return self.login(user)

    def authenticate(self, username: str, password: str) -> User:
        user = User.objects.get(username=username)
        if not user.check_password(password):
            raise User.DoesNotExist()
        return user

    def authenticate_by_token(
        self, token: str, is_active: typing.Optional[bool] = None
    ) -> typing.Tuple[typing.Optional[User], typing.Optional[str]]:
        user = None
        decoded_token = None

        kwargs = {}
        if isinstance(is_active, bool):
            kwargs["is_active"] = is_active

        try:
            decoded_token = self.auth.get_raw_jwt(token)
            user_id = utils.decode_id(decoded_token["sub"])
            user = User.objects.get(id=user_id, **kwargs)
        except User.DoesNotExist:
            logger.warning("User doesn't exist: %s", decoded_token)
        except JWTDecodeError as e:
            logger.warning("Fail to verify the token: %s", e.message)
        except ValueError as e:
            logger.warning("Malformed token: %s", e)
        except InvalidHeaderError as e:
            logger.warning("Invalid token header: %s", e.message)

        return user, decoded_token

    @staticmethod
    def generate_http_response(
        request,
        resp_cls: typing.Type[HttpResponseBase],
        refresh_token: str,
        resp_kwargs: typing.Dict = None,
        unpack_resp_kwargs: bool = False,
    ) -> HttpResponseBase:
        site = get_current_site(request)
        if resp_kwargs is None:
            resp_kwargs = {}

        if unpack_resp_kwargs:
            resp = resp_cls(**resp_kwargs)
        else:
            resp = resp_cls(resp_kwargs)
        resp.set_cookie(
            RefreshTokenCookieAuth.param_name,
            refresh_token,
            httponly=True,
            domain=site.domain.split(":", 1)[0],  # remove port
            samesite="Strict",
            max_age=timedelta(days=7).total_seconds(),
        )
        return resp
