from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, SessionLocal
from app.seed import run_seed
from app.routers import auth, users, subjects, challenges, leaderboard, achievements, antifraud, competitions, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="GeniUs API",
    description="Backend API for GeniUs - Gamified Study Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subjects.router)
app.include_router(challenges.router)
app.include_router(leaderboard.router)
app.include_router(achievements.router)
app.include_router(antifraud.router)
app.include_router(competitions.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {
        "app": "GeniUs API",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "endpoints": {
            "auth": "/api/auth",
            "users": "/api/users",
            "subjects": "/api/subjects",
            "challenges": "/api/challenges",
            "leaderboard": "/api/leaderboard",
            "achievements": "/api/achievements",
            "antifraud": "/api/antifraud",
            "competitions": "/api/competitions",
            "dashboard_api": "/api/dashboard",
            "dashboard_html": "/dashboard",
        },
    }
