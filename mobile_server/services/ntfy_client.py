import httpx

from mobile_server.config import settings


async def send_notification(
    message: str,
    title: str = "Claude 消息",
    priority: str = "default",
    tags: list[str] | None = None,
    topic: str | None = None,
) -> None:
    target_topic = topic or settings.ntfy_default_topic
    url = f"{settings.ntfy_base_url.rstrip('/')}/{target_topic}"

    headers: dict[str, str] = {
        "Title": title,
        "Priority": priority,
        "Content-Type": "text/plain; charset=utf-8",
    }
    if tags:
        headers["Tags"] = ",".join(tags)
    if settings.ntfy_auth_token:
        headers["Authorization"] = f"Bearer {settings.ntfy_auth_token}"

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(url, content=message.encode("utf-8"), headers=headers)
        response.raise_for_status()
