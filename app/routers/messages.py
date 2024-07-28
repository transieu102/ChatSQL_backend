from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from typing import List
from app import schemas, models
from app.database import get_db
from app.utils.dependencies import get_current_user
from sqlalchemy.exc import SQLAlchemyError
import json
from ..GPT import GPT
import sqlite3
router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/", response_model=schemas.Message)
def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        #check exist conversation
        check = db.query(models.Conversation).filter(models.Conversation.ConversationID == message.ConversationID ,
                                                    models.Conversation.UserID == current_user.UserID).first()
        if not check:
            raise HTTPException(status_code=400, detail="Conversation not found")
        db_message = models.Message(**message.model_dump())
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message
    except SQLAlchemyError as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.rollback()
        raise HTTPException(status_code=400, detail="An error occurred while sending the message: " + str(e))


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, con_id : int = Query(...), user_id: int = Query(...), db: Session = Depends(get_db)):
    #convert data
    current_user = db.query(models.User).filter(models.User.UserID == user_id).first()
    # current_user = schemas.User(**current_user)
    conversationID = schemas.ConversationID(ConversationID=con_id)

    await websocket.accept()
    gpt = GPT(current_user.API_Key)
    conversation = db.query(models.Conversation).filter(models.Conversation.ConversationID == conversationID.ConversationID).first()
    database = db.query(models.Database).filter(models.Database.DatabaseID == conversation.DatabaseID).first()
    message_history = read_messages(conversationID, db, current_user)
    gpt.init_context(database, message_history)
    try:
        while True:
            message = await websocket.receive_text()
            print(message)
            # message = {'index': 0, 'content': ''}
            message = json.loads(message)
            index = int(message['index']) #index of message in conversation
            if index < len(gpt.message_history):
                gpt.update_message_history(index = index)
                delete_messages_over_index(index, conversationID, db, current_user) #remove all message with index >= index
            
            content = message['content']
            new_message = schemas.MessageCreate(Index=index,Content=content, ConversationID=conversationID.ConversationID, Role="user")
            send_message(new_message, db, current_user)


            response = gpt.generate_response(new_message)
            bot_message = schemas.MessageCreate(Index=index+1,Content='', ConversationID=conversationID.ConversationID, Role="assistant")
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    # print(content)
                    bot_message.Content += content
                    await websocket.send_text(content)
            gpt.update_message_history(bot_message = bot_message)
            send_message(bot_message, db, current_user)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(e)
        raise(e)


@router.post("/get_by_conid", response_model=List[schemas.Message])
def read_messages(conversationID : schemas.ConversationID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    messages = db.query(models.Message).filter(models.Message.ConversationID == conversationID.ConversationID).order_by(asc(models.Message.Index)).all()
    return messages

def delete_messages_over_index( index : int, conversationID : schemas.ConversationID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        db.query(models.Message).filter(and_(models.Message.ConversationID == conversationID.ConversationID, models.Message.MessageID >= index)).delete()
        db.commit()
    except SQLAlchemyError as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.rollback()
        raise HTTPException(status_code=400, detail="An error occurred while deleting the messages: " + str(e))