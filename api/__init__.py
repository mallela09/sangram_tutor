# This file makes the api directory a package
# It can be used to export specific components if needed

# Import routers to make them available from the api package
from api.auth import router as auth_router
# You can uncomment these as they're implemented
# from api.users import router as users_router
# from api.learning import router as learning_router
# from api.analytics import router as analytics_router