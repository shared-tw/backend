import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import JWTDecodeError
from ninja import Router, Schema, errors
from ninja.security import HttpBearer

from . import schemas

logger = logging.getLogger(__name__)

User = get_user_model()
router = Router(tags=["Authentication"])


class Settings(Schema):
    authjwt_secret_key: str = settings.SECRET_KEY


@AuthJWT.load_config
def get_config():
    return Settings()


class JWTAuthBearer(HttpBearer):
    def authenticate(self, request, token):
        auth = AuthJWT()
        decoded_token = None
        try:
            decoded_token = auth.get_raw_jwt(token)
            request.user = User.objects.get(
                username=decoded_token["sub"], is_active=True
            )
        except User.DoesNotExist:
            logger.warning("User doesn't exist: %s", decoded_token)
        except JWTDecodeError as e:
            logger.warning("Fail to verify the token: %s", e.message)

        return decoded_token


@router.post("/token", response=schemas.JWTToken)
def create_jwt_token(request, payload: schemas.JWTTokenCreation):
    try:
        user = User.objects.get(username=payload.username)
        if not user.is_active:
            raise User.DoesNotExist()
        if not user.check_password(payload.password):
            raise User.DoesNotExist()

        auth = AuthJWT()
        return schemas.JWTToken(
            access=auth.create_access_token(subject=user.username),
            refresh=auth.create_refresh_token(subject=user.username),
        )
    except User.DoesNotExist:
        raise errors.HttpError(400, "Invalid username or password")


@router.post("/token/refresh", response=schemas.JWTToken)
def refresh_jwt_token(request, payload: schemas.JWTRefreshToken):
    auth = AuthJWT()

    try:
        decoded_token = auth.get_raw_jwt(payload.refresh)
        username = decoded_token["sub"]
        return schemas.JWTToken(
            access=auth.create_access_token(subject=username),
        )
    except Exception as e:
        logger.warning("fail to refresh JWT token: %s", e)
        raise errors.HttpError(400, "Fail to refresh JWT token")
