from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app import schemas, models
from app.database import get_db
from app.utils.security import verify_password, hash_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=schemas.LoginResponse)
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.Username == user.Username).first()
    if not db_user or not verify_password(user.Password, db_user.Password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    return schemas.LoginResponse(status="Login successful", user_info=db_user)

@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        hashed_password = hash_password(user.Password)
        db_user = models.User(Username=user.Username, Password=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return {"status": "Register successful"}
    except SQLAlchemyError as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.rollback()
        raise HTTPException(status_code=400, detail="An error occurred while registering the user: " + str(e))
@router.post("/apikey_update", response_model=schemas.LoginResponse)
def update_api_key(user: schemas.User, db: Session = Depends(get_db)):
    # Update API key
    try:
        db_user = db.query(models.User).filter(models.User.UserID == user.UserID).first()
        db_user.API_Key = user.API_Key
        db.commit()
        db.refresh(db_user)
        return schemas.LoginResponse(status="Update successful", user_info=db_user)
    except SQLAlchemyError as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.rollback()
        raise HTTPException(status_code=400, detail="An error occurred while updating the API key: " + str(e))
