from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database import Base, engine
from backend.routers import audit, metrics, simulation, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create all database tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Risk-Adjusted Revenue Recovery Copilot (Razorpay AI Buildathon 2026 - Track 03)",
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS Middleware to support Vite React development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(transactions.router)
app.include_router(simulation.router)
app.include_router(metrics.router)
app.include_router(audit.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "recoveriq-api"}


@app.get("/api/info")
def api_info():
    return {
        "project": "RecoverIQ",
        "description": "Risk-Adjusted Revenue Recovery Copilot",
        "track": "Razorpay AI Buildathon 2026 - Track 03",
        "docs_url": "/docs",
        "health": "OK",
        "llm_mode": settings.LLM_MODE,
        "seed": settings.SIMULATION_SEED,
        "notice": "DEMO SYSTEM: ALL DATA IS SYNTHETIC. NO REAL MONEY MOVEMENT.",
    }


# Mount compiled React frontend if present
dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return api_info()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
