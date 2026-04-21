from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from mobile_server.config import settings

scheduler = AsyncIOScheduler(
    jobstores={
        "default": SQLAlchemyJobStore(url=f"sqlite:///{settings.db_path}", tablename="apscheduler_jobs")
    },
    timezone=settings.timezone,
)


async def _send_scheduled(title: str, message: str, priority: str, tags: list[str], topic: str | None) -> None:
    from mobile_server.services.ntfy_client import send_notification
    await send_notification(message=message, title=title, priority=priority, tags=tags, topic=topic)
