"""GET /health: liveness for monitoring and keep-alive pings."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
