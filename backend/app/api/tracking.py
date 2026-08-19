"""Public (unauthenticated) tracking endpoints — hit by recipients' mail clients."""
import base64

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.tracking_service import record_click, record_open, record_unsubscribe

router = APIRouter(prefix="/api/track", tags=["tracking"])

# 1x1 transparent GIF
PIXEL = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7")


@router.get("/open/{tracking_id}")
def track_open(tracking_id: str, request: Request, db: Session = Depends(get_db)):
    record_open(
        db,
        tracking_id,
        ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", ""),
    )
    return Response(content=PIXEL, media_type="image/gif")


@router.get("/click/{tracking_id}")
def track_click(tracking_id: str, url: str, db: Session = Depends(get_db)):
    record_click(db, tracking_id, url)
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return RedirectResponse(url=url, status_code=302)


@router.get("/unsubscribe/{tracking_id}")
def unsubscribe(tracking_id: str, db: Session = Depends(get_db)):
    record_unsubscribe(db, tracking_id)
    return Response(content="You have been unsubscribed.", media_type="text/plain")
