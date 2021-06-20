from ninja import NinjaAPI
from ninja.operation import Operation

from authenticator.api import JWTAuthBearer
from authenticator.api import router as authenticator_router
from oauth2.api import router as oauth_router
from share.api import router as share_router


class SharedTWApi(NinjaAPI):
    def get_openapi_operation_id(self, operation: Operation) -> str:
        name = operation.view_func.__name__
        return name.replace(".", "_")


api = SharedTWApi(title="shared-tw API", version="0.1.0")

api.add_router("auth", authenticator_router)
api.add_router("oauth", oauth_router)
api.add_router("", share_router, auth=JWTAuthBearer())
