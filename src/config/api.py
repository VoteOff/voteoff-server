from ninja import NinjaAPI

from user.api import router as user_router
from vote.api import router as vote_router

from django.conf import settings
from .schema import VersionResponse

api = NinjaAPI(
    title="Vote The Bowl API",
    version="0.4.0",
    docs_url=("/docs/" if settings.DEBUG else None),
)

api.add_router("/user/", user_router)
api.add_router("/vote/", vote_router)

# Add more routers as needed


@api.get("/version/", response=VersionResponse, tags=["API Info"])
async def version(request):
    return {"version": api.version}
