from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "EMOS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
