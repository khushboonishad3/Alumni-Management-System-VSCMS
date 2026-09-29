import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.seed_data import seed_database
from app.routers import (
    auth_router,
    users_router,
    jobs_router,
    mentorship_router,
    projects_router,
    resources_router,
    events_router,
    communication_router,
    admin_router,
    search_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist and default seed data is ready
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Production-ready BCA & MCA Alumni Management, Developer Networking, Mentorship & Placement Platform for Dr. Virendra Swarup College of Management Studies (CMS Kanpur).",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static & Media files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# Include Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(jobs_router)
app.include_router(mentorship_router)
app.include_router(projects_router)
app.include_router(resources_router)
app.include_router(events_router)
app.include_router(communication_router)
app.include_router(admin_router)
app.include_router(search_router)

# Frontend UI Root & Auth Route
@app.get("/", response_class=HTMLResponse)
@app.get("/auth", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>CMS Kanpur Alumni Networking Platform Backend Active.</h1>")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "college": settings.COLLEGE_NAME,
        "platform": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
