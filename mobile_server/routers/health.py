from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

from mobile_server.config import settings
from mobile_server.database import get_db
from mobile_server.scheduler import scheduler

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    with get_db() as conn:
        todo_count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
        paper_count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        routine_count = conn.execute("SELECT COUNT(*) FROM routines WHERE enabled=1").fetchone()[0]
    return {
        "status": "ok",
        "scheduled_jobs": len(scheduler.get_jobs()),
        "todo_count": todo_count,
        "paper_count": paper_count,
        "active_routines": routine_count,
        "ntfy_topic": settings.ntfy_default_topic,
    }


@router.get("/dashboard", include_in_schema=False)
async def dashboard():
    path = os.path.join(os.path.dirname(__file__), "..", "static", "dashboard.html")
    return FileResponse(os.path.abspath(path))
