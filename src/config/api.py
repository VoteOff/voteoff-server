from ninja import NinjaAPI

from user.api import router as user_router
from vote.api import router as vote_router

api = NinjaAPI()

api.add_router("/user/", user_router)
api.add_router("/vote/", vote_router)

# Add more routers as needed