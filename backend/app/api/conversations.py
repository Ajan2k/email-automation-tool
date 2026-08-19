from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database.connection import get_db
from app.models import Conversation, EmailMessage, User
from app.schemas.conversation import ConversationDetail, ConversationOut

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    status: str = "",
    classification: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Conversation).where(Conversation.owner_id == user.id)
    if status:
        stmt = stmt.where(Conversation.status == status)
    if classification:
        stmt = stmt.where(Conversation.classification == classification)
    return db.execute(stmt.order_by(Conversation.last_message_at.desc())).scalars().all()


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.execute(
        select(EmailMessage)
        .where(EmailMessage.conversation_id == conversation_id)
        .order_by(EmailMessage.id)
    ).scalars().all()
    detail = ConversationDetail.model_validate(conversation)
    detail.messages = messages
    return detail
