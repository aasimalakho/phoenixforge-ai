from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.database import init_db
from .routes import incidents, dashboard

app = FastAPI(
    title="PhoenixForge AI",
    description="Self-healing data systems powered by DataHub",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for a hackathon demo; lock this down for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    from .config import settings
    return {
        "status": "ok",
        "demo_mode": settings.DEMO_MODE,
        "llm_enabled": bool(settings.ANTHROPIC_API_KEY),
        "github_enabled": bool(settings.GITHUB_TOKEN and settings.GITHUB_REPO),
    }
