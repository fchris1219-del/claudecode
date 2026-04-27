import uuid
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from mobile_server.auth import verify_api_key
from mobile_server.models import ScheduleRequest, ScheduleResponse
from mobile_server.scheduler import scheduler, _send_scheduled

router = APIRouter(tags=["schedule"])


@router.post("/schedule", response_model=ScheduleResponse, dependencies=[Depends(verify_api_key)])
async def create_schedule(req: ScheduleRequest):
    if not req.run_at and not req.cron:
        raise HTTPException(status_code=422, detail="必须提供 run_at 或 cron")

    job_id = str(uuid.uuid4())
    kwargs = dict(
        title=req.title,
        message=req.message,
        priority=req.priority,
        tags=req.tags,
        topic=None,
    )

    if req.cron:
        trigger = CronTrigger.from_crontab(req.cron, timezone=scheduler.timezone)
        scheduler.add_job(_send_scheduled, trigger=trigger, kwargs=kwargs, id=job_id)
        return ScheduleResponse(job_id=job_id, run_at=None, cron=req.cron, status="scheduled")

    # one-shot
    run_at = req.run_at
    if run_at.tzinfo is None:
        run_at = run_at.replace(tzinfo=scheduler.timezone)
    trigger = DateTrigger(run_date=run_at)
    scheduler.add_job(_send_scheduled, trigger=trigger, kwargs=kwargs, id=job_id)
    return ScheduleResponse(job_id=job_id, run_at=run_at.isoformat(), cron=None, status="scheduled")


@router.get("/schedule", dependencies=[Depends(verify_api_key)])
async def list_schedules():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "job_id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    return {"jobs": jobs}


@router.delete("/schedule/{job_id}", dependencies=[Depends(verify_api_key)])
async def delete_schedule(job_id: str):
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    scheduler.remove_job(job_id)
    return {"status": "deleted", "job_id": job_id}
