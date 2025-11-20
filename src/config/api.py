from ninja import NinjaAPI

from user.api import router as user_router
from vote.api import router as vote_router

from django.conf import settings

api = NinjaAPI(
    title="Vote The Bowl API",
    version="1.0.0",
    docs_url=("/docs/" if settings.DEBUG else None),
)

api.add_router("/user/", user_router)
api.add_router("/vote/", vote_router)

# Add more routers as needed
