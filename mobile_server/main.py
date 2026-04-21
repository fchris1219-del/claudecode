from contextlib import asynccontextmanager

from fastapi import FastAPI

from mobile_server.database import init_db
from mobile_server.scheduler import scheduler
from mobile_server.routers import health, notifications, todos, schedule


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Mobile Messaging Server", version="1.0.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(notifications.router)
app.include_router(schedule.router)
app.include_router(todos.router)
