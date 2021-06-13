from ninja import NinjaAPI
from ninja.operation import Operation

from authenticator.api import JWTAuthBearer, JWTAuthUserBearer
from authenticator.api import router as authenticator_router
from share.api import organization_router, public_router, register_rotuer


class SharedTWApi(NinjaAPI):
    def get_openapi_operation_id(self, operation: Operation) -> str:
        name = operation.view_func.__name__
        return name.replace(".", "_")


api = SharedTWApi(title="shared-tw API", version="0.1.0")

api.add_router("", public_router)
api.add_router("auth", authenticator_router)
api.add_router("register", register_rotuer, auth=JWTAuthBearer())
api.add_router("organization", organization_router, auth=JWTAuthUserBearer())
