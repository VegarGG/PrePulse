from fastapi import APIRouter

from backend import store

router = APIRouter()


@router.get("/dashboard/metrics")
async def get_metrics() -> dict:
    return store.aggregate_metrics()
