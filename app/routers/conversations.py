from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List
from app import schemas, models
from app.database import get_db
from app.utils.dependencies import get_current_user

from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("/create", response_model=schemas.Conversation)
def create_conversation(
    conversation: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        # Sử dụng `model_dump` thay vì `dict`
        # check dbId và uid
        check = db.query(models.Database).filter(and_(models.Database.DatabaseID == conversation.DatabaseID,
                                                  models.Database.UserID == current_user.UserID,
                                                  conversation.UserID == current_user.UserID)).first()
        if not check:
            raise HTTPException(status_code=400, detail="Database not found")
        db_conversation = models.Conversation(**conversation.model_dump())
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation
    except SQLAlchemyError as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.rollback()
        raise HTTPException(status_code=400, detail="An error occurred while creating the conversation: " + str(e))

@router.post("/get_by_uid", response_model=List[schemas.Conversation])
def get_list_conversations( db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    conversations = db.query(models.Conversation).filter(models.Conversation.UserID == current_user.UserID).order_by(
        desc(models.Conversation.LastModified)
    ).all()
    return conversations

@router.post("/delete_conversation", response_model=List[schemas.Conversation])
def delete_conversation(conversation: schemas.Conversation, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    #Delete all messages in this conversation
    db.query(models.Message).filter(models.Message.ConversationID == conversation.ConversationID).delete()
    db.query(models.Conversation).filter(models.Conversation.ConversationID == conversation.ConversationID).delete()
    db.commit()
    return get_list_conversations(db, current_user)

@router.post("/conversation_info")
def conversation_info(conversation: schemas.ConversationID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    conver = db.query(models.Conversation).filter(models.Conversation.ConversationID == conversation.ConversationID).first()
    database = db.query(models.Database).filter(models.Database.DatabaseID == conver.DatabaseID).first()
    return {"conversation": conver, "database": database}