from ninja import NinjaAPI

from authenticator.api import JWTAuthBearer
from authenticator.api import router as authenticator_router
from share.api import organization_router, public_router, register_rotuer

api = NinjaAPI(title="shared-tw API", version="0.1.0")

api.add_router("", public_router)
api.add_router("auth", authenticator_router)
api.add_router("register", register_rotuer)
api.add_router("organization", organization_router, auth=JWTAuthBearer())
