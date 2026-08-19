from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models import Campaign, CampaignStatus, User
from app.schemas.campaign import CampaignCreate, CampaignOut, CampaignStats
from app.services.analytics_service import campaign_stats
from app.services.campaign_service import create_campaign, launch_campaign

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def _get_owned(campaign_id: int, db: Session, user: User) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None or campaign.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("", response_model=list[CampaignOut])
def list_campaigns(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.execute(
        select(Campaign).where(Campaign.owner_id == user.id).order_by(Campaign.id.desc())
    ).scalars().all()


@router.post("", response_model=CampaignOut, status_code=201)
def create(data: CampaignCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_campaign(db, user.id, data)


@router.get("/{campaign_id}", response_model=CampaignOut)
def get(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_owned(campaign_id, db, user)


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
def stats(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned(campaign_id, db, user)
    return campaign_stats(db, campaign_id)


@router.post("/{campaign_id}/launch", response_model=CampaignOut)
def launch(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaign = _get_owned(campaign_id, db, user)
    if campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.SCHEDULED, CampaignStatus.PAUSED):
        raise HTTPException(status_code=409, detail=f"Cannot launch campaign in state {campaign.status}")
    try:
        launch_campaign(db, campaign)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignOut)
def pause(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaign = _get_owned(campaign_id, db, user)
    campaign.status = CampaignStatus.PAUSED
    db.commit()
    db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/cancel", response_model=CampaignOut)
def cancel(campaign_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaign = _get_owned(campaign_id, db, user)
    campaign.status = CampaignStatus.CANCELLED
    db.commit()
    db.refresh(campaign)
    return campaign
