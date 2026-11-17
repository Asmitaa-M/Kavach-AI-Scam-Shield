import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config import get_settings
from app.database.db import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_):
    init_db()
    yield


app = FastAPI(title="Kavach API", version="0.1.0", lifespan=lifespan,
              description="Family scam shield. Analysis aid only - cannot block or reverse payments.")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in get_settings().cors_origins.split(",")],
                   allow_methods=["*"], allow_headers=["*"], allow_credentials=False)
app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    s = get_settings()
    from app.services.tier1.classifier import get_model
    return {"status": "ok", "ml_model_loaded": get_model() is not None,
            "integrations": {"gemini": bool(s.gemini_api_key), "safe_browsing": bool(s.safe_browsing_api_key),
                             "virustotal": bool(s.virustotal_api_key)}}
