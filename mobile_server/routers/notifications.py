from fastapi import APIRouter, Depends, HTTPException

from mobile_server.auth import verify_api_key
from mobile_server.models import NotifyRequest
from mobile_server.services.ntfy_client import send_notification

router = APIRouter(tags=["notifications"])


@router.post("/notify", dependencies=[Depends(verify_api_key)])
async def notify(req: NotifyRequest):
    try:
        await send_notification(
            message=req.message,
            title=req.title,
            priority=req.priority,
            tags=req.tags,
            topic=req.topic,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ntfy 推送失败: {e}")
    return {"status": "sent", "title": req.title}
