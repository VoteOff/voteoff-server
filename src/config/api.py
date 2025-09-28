from ninja import NinjaAPI

from user.api import router as user_router

api = NinjaAPI()

api.add_router("/user/", user_router)

# Add more routers as needed