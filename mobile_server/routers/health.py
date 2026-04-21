from fastapi import APIRouter

from mobile_server.config import settings
from mobile_server.database import get_db
from mobile_server.scheduler import scheduler

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    with get_db() as conn:
        todo_count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    return {
        "status": "ok",
        "scheduled_jobs": len(scheduler.get_jobs()),
        "todo_count": todo_count,
        "ntfy_topic": settings.ntfy_default_topic,
    }
