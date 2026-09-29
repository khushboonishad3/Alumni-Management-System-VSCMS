from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.jobs import router as jobs_router
from app.routers.mentorship import router as mentorship_router
from app.routers.projects import router as projects_router
from app.routers.resources import router as resources_router
from app.routers.events import router as events_router
from app.routers.communication import router as communication_router
from app.routers.admin import router as admin_router
from app.routers.search import router as search_router

__all__ = [
    "auth_router",
    "users_router",
    "jobs_router",
    "mentorship_router",
    "projects_router",
    "resources_router",
    "events_router",
    "communication_router",
    "admin_router",
    "search_router"
]
