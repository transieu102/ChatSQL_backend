from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import User as UserSchema

def get_current_user(user_info: UserSchema, db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.UserID == user_info.UserID).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user
