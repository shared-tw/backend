from ninja import NinjaAPI

from authenticator.api import JWTAuthBearer
from authenticator.api import router as authenticator_router
from share.api import router as share_router

api = NinjaAPI(title="shared-tw API", version="0.1.0")

api.add_router("auth", authenticator_router)
api.add_router("", share_router, auth=JWTAuthBearer())
