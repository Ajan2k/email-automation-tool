"""Public (unauthenticated) tracking endpoints — hit by recipients' mail clients."""
import base64

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db
from app.services.tracking_service import record_click, record_open, record_unsubscribe

router = APIRouter(tags=["tracking"])

# 1x1 transparent GIF
PIXEL = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


@router.get("/api/track/open/{tracking_id}")
@router.get("/api/tracking/open/{tracking_id}")
@router.get("/api/v1/tracking/open/{tracking_id}")
def track_open(tracking_id: str, request: Request, db: Session = Depends(get_db)):
    record_open(
        db,
        tracking_id,
        ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )
    return Response(content=PIXEL, media_type="image/gif")


@router.get("/api/track/click/{tracking_id}")
@router.get("/api/tracking/click/{tracking_id}")
@router.get("/api/v1/tracking/click/{tracking_id}")
def track_click(tracking_id: str, url: str = "", db: Session = Depends(get_db)):
    target_url = url.strip() or settings.public_api_url
    record_click(db, tracking_id, target_url)
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url
    return RedirectResponse(url=target_url, status_code=302)


@router.get("/api/track/unsubscribe/{tracking_id}")
@router.get("/api/tracking/unsubscribe/{tracking_id}")
@router.get("/api/v1/tracking/unsubscribe/{tracking_id}")
def unsubscribe(tracking_id: str, db: Session = Depends(get_db)):
    record_unsubscribe(db, tracking_id)
    return Response(content="You have been unsubscribed.", media_type="text/plain")


@router.post("/api/v1/tracking/heartbeat")
@router.post("/api/track/heartbeat")
@router.post("/api/tracking/heartbeat")
def tracking_heartbeat():
    return {"status": "ok"}


@router.post("/api/v1/tracking/idle-logs")
@router.post("/api/track/idle-logs")
@router.post("/api/tracking/idle-logs")
def tracking_idle_logs():
    return {"status": "ok"}
