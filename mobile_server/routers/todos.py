from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from mobile_server.auth import verify_api_key
from mobile_server.database import get_db, now_iso
from mobile_server.models import TodoCreate, TodoUpdate, TodoResponse

router = APIRouter(tags=["todos"])


def _row_to_response(row) -> TodoResponse:
    return TodoResponse(
        id=row["id"],
        title=row["title"],
        notes=row["notes"],
        due_date=row["due_date"],
        priority=row["priority"],
        list=row["list"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.post("/todos", response_model=TodoResponse, dependencies=[Depends(verify_api_key)])
async def create_todo(todo: TodoCreate):
    ts = now_iso()
    due = todo.due_date.isoformat() if todo.due_date else None
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO todos (title, notes, due_date, priority, list, completed, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 0, ?, ?)",
            (todo.title, todo.notes, due, todo.priority, todo.list, ts, ts),
        )
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _row_to_response(row)


@router.get("/todos", response_model=list[TodoResponse], dependencies=[Depends(verify_api_key)])
async def list_todos(
    list: Optional[str] = None,
    completed: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
):
    query = "SELECT * FROM todos WHERE 1=1"
    params: list = []
    if list is not None:
        query += " AND list = ?"
        params.append(list)
    if completed is not None:
        query += " AND completed = ?"
        params.append(1 if completed else 0)
    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_response(r) for r in rows]


@router.patch("/todos/{todo_id}", response_model=TodoResponse, dependencies=[Depends(verify_api_key)])
async def update_todo(todo_id: int, update: TodoUpdate):
    fields: list[str] = []
    params: list = []

    if update.title is not None:
        fields.append("title = ?"); params.append(update.title)
    if update.notes is not None:
        fields.append("notes = ?"); params.append(update.notes)
    if update.due_date is not None:
        fields.append("due_date = ?"); params.append(update.due_date.isoformat())
    if update.priority is not None:
        fields.append("priority = ?"); params.append(update.priority)
    if update.list is not None:
        fields.append("list = ?"); params.append(update.list)
    if update.completed is not None:
        fields.append("completed = ?"); params.append(1 if update.completed else 0)

    if not fields:
        raise HTTPException(status_code=422, detail="没有提供任何更新字段")

    fields.append("updated_at = ?"); params.append(now_iso())
    params.append(todo_id)

    with get_db() as conn:
        conn.execute(f"UPDATE todos SET {', '.join(fields)} WHERE id = ?", params)
        row = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Todo 不存在")
    return _row_to_response(row)


@router.delete("/todos/{todo_id}", dependencies=[Depends(verify_api_key)])
async def delete_todo(todo_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT id FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Todo 不存在")
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    return {"status": "deleted", "id": todo_id}
