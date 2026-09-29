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
    try:
        Base.metadata.create_all(bind=engine)
        seed_database()
    except Exception as e:
        print(f"[STARTUP DB INITIALIZATION WARNING] {e}")
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

# Mount Static & Media files safely using resolved paths
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_PATH, "static")
media_dir = os.path.join(BASE_PATH, "media")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
if os.path.exists(media_dir):
    app.mount("/media", StaticFiles(directory=media_dir), name="media")

# Vercel Serverless Path Unmasking Middleware
@app.middleware("http")
async def vercel_routing_middleware(request: Request, call_next):
    raw_path = request.scope.get("path", "")
    if raw_path in ["/main.py", "/main", "/api/index", "/api/index.py"] or raw_path.startswith(("/main.py/", "/api/index/")):
        matched = request.headers.get("x-matched-path") or request.headers.get("x-forwarded-uri")
        if matched and not matched.startswith(("/main.py", "/api/index")):
            clean_path = matched.split("?")[0]
            request.scope["path"] = clean_path if clean_path else "/"
        else:
            request.scope["path"] = "/"
    return await call_next(request)

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
@app.get("/main.py", response_class=HTMLResponse)
@app.get("/main", response_class=HTMLResponse)
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
