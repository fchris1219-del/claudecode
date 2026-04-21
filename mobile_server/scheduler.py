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


async def job_evening_keyword_prompt() -> None:
    """Every evening: push a notification asking for tomorrow's search keywords."""
    from mobile_server.services.ntfy_client import send_notification
    from mobile_server.config import settings as cfg

    # ntfy actions let the notification open a Shortcut directly
    topic = cfg.ntfy_default_topic
    import httpx
    headers = {
        "Title": "今晚的论文关键词",
        "Priority": "default",
        "Tags": "books",
        "Actions": "view, 提交关键词, shortcuts://run-shortcut?name=提交论文关键词",
        "Content-Type": "text/plain; charset=utf-8",
    }
    if cfg.ntfy_auth_token:
        headers["Authorization"] = f"Bearer {cfg.ntfy_auth_token}"
    url = f"{cfg.ntfy_base_url.rstrip('/')}/{topic}"
    msg = "你想明天检索哪方面的社会学论文？点击按钮打开快捷指令提交关键词。"
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(url, content=msg.encode("utf-8"), headers=headers)


async def job_morning_paper_search() -> None:
    """Every morning: fetch yesterday's keywords, search papers, summarize, push."""
    import json
    from mobile_server.database import get_db, now_iso
    from mobile_server.services.semantic_scholar import search_papers
    from mobile_server.services.claude_client import summarize_papers, discuss_papers
    from mobile_server.services.ntfy_client import send_notification

    # Get the latest unused keywords
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM keywords WHERE used = 0 ORDER BY created_at DESC LIMIT 1"
        ).fetchone()

    if not row:
        await send_notification(
            message="今天没有找到待检索的关键词，请昨晚提交关键词后再试。",
            title="论文检索提醒",
            priority="low",
            tags=["warning"],
        )
        return

    kw_id = row["id"]
    keywords = row["keywords"]
    search_date = row["date"]

    try:
        papers = await search_papers(keywords, limit=6)
    except Exception as e:
        await send_notification(
            message=f"Semantic Scholar 检索失败：{e}",
            title="论文检索错误",
            priority="high",
            tags=["x"],
        )
        return

    if not papers:
        await send_notification(
            message=f"关键词「{keywords}」未检索到论文，请尝试其他关键词。",
            title="论文检索结果",
            priority="default",
            tags=["mag"],
        )
        return

    # Save papers to DB
    ts = now_iso()
    with get_db() as conn:
        for p in papers:
            conn.execute(
                "INSERT INTO papers (search_date, keywords, title, abstract, authors, year, url, pdf_url, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    search_date, keywords, p["title"], p.get("abstract", ""),
                    json.dumps(p.get("authors", []), ensure_ascii=False),
                    p.get("year"), p.get("url"), p.get("pdf_url"), ts,
                ),
            )
        conn.execute("UPDATE keywords SET used = 1 WHERE id = ?", (kw_id,))

    # Generate summary and discussion via Claude
    try:
        summary = await summarize_papers(papers)
        discussion = await discuss_papers(papers, keywords)
    except Exception as e:
        summary = "\n".join(f"[{i+1}] {p['title']}" for i, p in enumerate(papers))
        discussion = f"（AI 分析暂时不可用：{e}）"

    # Push summary notification
    await send_notification(
        message=f"关键词：{keywords}\n\n{summary}",
        title=f"今日论文摘要（{len(papers)}篇）",
        priority="default",
        tags=["books"],
    )

    # Push discussion as a second notification
    if discussion:
        await send_notification(
            message=discussion,
            title="论文主题讨论",
            priority="low",
            tags=["bulb"],
        )


def register_routine_jobs(routine_states: list[dict]) -> None:
    """Register or update scheduled jobs based on DB routine states."""
    job_map = {
        "evening_keyword_prompt": job_evening_keyword_prompt,
        "morning_paper_search": job_morning_paper_search,
    }
    for r in routine_states:
        rid = r["id"]
        fn = job_map.get(rid)
        if fn is None:
            continue
        existing = scheduler.get_job(rid)
        if r["enabled"] and not existing:
            from apscheduler.triggers.cron import CronTrigger
            trigger = CronTrigger.from_crontab(r["cron"], timezone=scheduler.timezone)
            scheduler.add_job(fn, trigger=trigger, id=rid, replace_existing=True)
        elif not r["enabled"] and existing:
            scheduler.remove_job(rid)
