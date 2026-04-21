from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# --- Notification models ---

class NotifyRequest(BaseModel):
    title: str = "Claude 消息"
    message: str
    priority: str = "default"  # min | low | default | high | urgent
    tags: list[str] = []
    topic: Optional[str] = None  # overrides default topic


class ScheduleRequest(BaseModel):
    title: str = "定时提醒"
    message: str
    priority: str = "default"
    tags: list[str] = []
    run_at: Optional[datetime] = None   # one-shot, ISO8601
    cron: Optional[str] = None          # recurring, e.g. "0 9 * * 1-5"


class ScheduleResponse(BaseModel):
    job_id: str
    run_at: Optional[str]
    cron: Optional[str]
    status: str


# --- Todo models ---

class TodoCreate(BaseModel):
    title: str
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: int = 0       # 0=none 1=low 2=medium 3=high
    list: str = "Inbox"


class TodoUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = None
    list: Optional[str] = None
    completed: Optional[bool] = None


class TodoResponse(BaseModel):
    id: int
    title: str
    notes: Optional[str]
    due_date: Optional[str]
    priority: int
    list: str
    completed: bool
    created_at: str
    updated_at: str
