from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from mobile_server.database import init_db, get_db
from mobile_server.scheduler import scheduler, register_routine_jobs
from mobile_server.routers.routines import seed_routines
from mobile_server.routers import health, notifications, todos, schedule, routines


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_routines()

    # Load routine states from DB and register scheduled jobs
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM routines").fetchall()
    register_routine_jobs([dict(r) for r in rows])

    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Mobile Messaging Server", version="2.0.0", lifespan=lifespan)

# Serve dashboard static files
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

app.include_router(health.router)
app.include_router(notifications.router)
app.include_router(schedule.router)
app.include_router(todos.router)
app.include_router(routines.router)
