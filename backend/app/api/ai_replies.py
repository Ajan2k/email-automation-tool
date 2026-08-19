from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models import AIReplyDraft, AIReplyStatus, Conversation, User
from app.schemas.conversation import AIReplyOut, AIReplyUpdate
from app.services.ai_reply_service import approve_and_queue, generate_draft

router = APIRouter(prefix="/api/ai-replies", tags=["ai-replies"])


def _get_owned(draft_id: int, db: Session, user: User) -> AIReplyDraft:
    draft = db.get(AIReplyDraft, draft_id)
    if draft is None or draft.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.get("", response_model=list[AIReplyOut])
def list_drafts(
    status: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(AIReplyDraft).where(AIReplyDraft.owner_id == user.id)
    if status:
        stmt = stmt.where(AIReplyDraft.status == status)
    return db.execute(stmt.order_by(AIReplyDraft.id.desc())).scalars().all()


@router.patch("/{draft_id}", response_model=AIReplyOut)
def edit_draft(
    draft_id: int,
    data: AIReplyUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    draft = _get_owned(draft_id, db, user)
    if draft.status != AIReplyStatus.DRAFT:
        raise HTTPException(status_code=409, detail="Only drafts can be edited")
    if data.edited_body is not None:
        draft.edited_body = data.edited_body
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/{draft_id}/regenerate", response_model=AIReplyOut)
def regenerate(draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    draft = _get_owned(draft_id, db, user)
    conversation = db.get(Conversation, draft.conversation_id)
    draft.status = AIReplyStatus.REJECTED
    db.commit()
    return generate_draft(db, conversation)


@router.post("/{draft_id}/reject", response_model=AIReplyOut)
def reject(draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    draft = _get_owned(draft_id, db, user)
    draft.status = AIReplyStatus.REJECTED
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/{draft_id}/approve")
def approve(draft_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """HUMAN APPROVAL GATE — the only path that queues an AI reply for sending."""
    draft = _get_owned(draft_id, db, user)
    if draft.status != AIReplyStatus.DRAFT:
        raise HTTPException(status_code=409, detail="Draft already reviewed")
    email = approve_and_queue(db, draft)
    return {"status": "queued", "email_id": email.id, "draft_id": draft.id}
