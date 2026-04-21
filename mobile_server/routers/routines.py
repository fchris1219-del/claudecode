import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from mobile_server.auth import verify_api_key
from mobile_server.config import settings
from mobile_server.database import get_db, now_iso

router = APIRouter(tags=["routines"])

# Predefined routines — seeded into DB on first run
_DEFAULT_ROUTINES = [
    {
        "id": "evening_keyword_prompt",
        "name": "晚间关键词询问",
        "description": "每晚推送提示，询问明天想搜索的论文关键词",
        "enabled": 1,
        "cron": settings.evening_prompt_cron,
    },
    {
        "id": "morning_paper_search",
        "name": "早间论文检索",
        "description": "每早根据前一晚提交的关键词检索 Semantic Scholar，AI 总结后推送",
        "enabled": 1,
        "cron": settings.morning_search_cron,
    },
]


def seed_routines() -> None:
    ts = now_iso()
    with get_db() as conn:
        for r in _DEFAULT_ROUTINES:
            conn.execute(
                "INSERT OR IGNORE INTO routines (id, name, description, enabled, cron, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (r["id"], r["name"], r["description"], r["enabled"], r["cron"], ts),
            )


# --- Models ---

class KeywordSubmit(BaseModel):
    keywords: str


class RoutineUpdate(BaseModel):
    enabled: Optional[bool] = None
    cron: Optional[str] = None


# --- Helpers ---

def _row_to_dict(row) -> dict:
    return dict(row)


# --- Endpoints ---

@router.get("/routines", dependencies=[Depends(verify_api_key)])
async def list_routines():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM routines ORDER BY id").fetchall()
    return {"routines": [_row_to_dict(r) for r in rows]}


@router.post("/routines/{routine_id}/toggle", dependencies=[Depends(verify_api_key)])
async def toggle_routine(routine_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM routines WHERE id = ?", (routine_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Routine 不存在")
        new_state = 0 if row["enabled"] else 1
        conn.execute(
            "UPDATE routines SET enabled = ?, updated_at = ? WHERE id = ?",
            (new_state, now_iso(), routine_id),
        )
        row = conn.execute("SELECT * FROM routines WHERE id = ?", (routine_id,)).fetchone()
    return {"routine": _row_to_dict(row)}


@router.patch("/routines/{routine_id}", dependencies=[Depends(verify_api_key)])
async def update_routine(routine_id: str, body: RoutineUpdate):
    fields, params = [], []
    if body.enabled is not None:
        fields.append("enabled = ?"); params.append(1 if body.enabled else 0)
    if body.cron is not None:
        fields.append("cron = ?"); params.append(body.cron)
    if not fields:
        raise HTTPException(status_code=422, detail="没有提供更新字段")
    fields.append("updated_at = ?"); params.append(now_iso())
    params.append(routine_id)
    with get_db() as conn:
        conn.execute(f"UPDATE routines SET {', '.join(fields)} WHERE id = ?", params)
        row = conn.execute("SELECT * FROM routines WHERE id = ?", (routine_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Routine 不存在")
    return {"routine": _row_to_dict(row)}


@router.post("/routines/keywords", dependencies=[Depends(verify_api_key)])
async def submit_keywords(body: KeywordSubmit):
    today = date.today().isoformat()
    ts = now_iso()
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO keywords (date, keywords, used, created_at) VALUES (?, ?, 0, ?)",
            (today, body.keywords.strip(), ts),
        )
        row_id = cur.lastrowid
    return {"id": row_id, "date": today, "keywords": body.keywords.strip(), "status": "saved"}


@router.get("/routines/papers/latest", dependencies=[Depends(verify_api_key)])
async def get_latest_papers(limit: int = 10):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM papers ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    papers = []
    for r in rows:
        d = _row_to_dict(r)
        d["authors"] = json.loads(d["authors"]) if d.get("authors") else []
        papers.append(d)
    return {"papers": papers, "count": len(papers)}


@router.get("/routines/keywords/latest", dependencies=[Depends(verify_api_key)])
async def get_latest_keywords():
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM keywords ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    if not row:
        return {"keywords": None}
    return _row_to_dict(row)
