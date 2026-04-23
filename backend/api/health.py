import os

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": "0.2.0",
        "mode": "live" if os.getenv("PREPULSE_LIVE") == "1" else "mock",
    }
