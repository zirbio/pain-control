from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers import analysis, entries, imports
from backend.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Pain Control API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entries.router)
app.include_router(imports.router)
app.include_router(analysis.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
