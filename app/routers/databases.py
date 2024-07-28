from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from app import schemas, models
from app.database import get_db
from app.utils.dependencies import get_current_user
from sqlalchemy.exc import SQLAlchemyError
import os
import shutil
import uuid
import json
import pandas as pd
import sqlite3
from io import StringIO
from ..GPT import GPT
from .conversations import delete_conversation
router = APIRouter(prefix="/databases", tags=["databases"])

@router.post("/create", response_model=List[schemas.Database])
async def create_database(
    database: str = Form(...),  
    files: list[UploadFile] = [],
    user_info: str = Form(...),  
    db: Session = Depends(get_db),
    ):
    # return []
    current_user_json = json.loads(user_info)
    database_json = json.loads(database)
    if not len(files) and not database_json['url']:
        raise HTTPException(status_code=400, detail="File or URL is required")
    try:
        current_user = schemas.User(**current_user_json)
        database = schemas.DatabaseCreate(**database_json)
        # Kiểm tra xem UserID có tồn tại trong bảng User hay không
        user = db.query(models.User).filter(models.User.UserID == database.UserID).first()
        if not user or user.UserID != current_user.UserID:
            raise HTTPException(status_code=400, detail="UserID Error")
        
        attribute = database.model_dump()
        print("attribute:",attribute)
        if attribute.get("url") is None and files:
            save_path = f"uploads/{current_user.UserID}/{attribute.get('DataName').replace(' ', '_')}_{str(uuid.uuid4())}"
            if not os.path.exists(save_path):
                os.makedirs(save_path)
                os.makedirs(save_path+"/original")
            database_connection = sqlite3.connect(save_path+"/database.db")
            cols_info = {}
            for file in files:
                content = await file.read()
                csv_file = StringIO(content.decode('utf-8'))
                df = pd.read_csv(csv_file)
                columns = list(df.columns)
                cols_info[file.filename.replace('.csv', '')] = columns
                df.to_sql(file.filename.replace('.csv', ''), database_connection, if_exists='replace', index=False)
                with open(f"{save_path}/original/{file.filename}", "wb") as f:
                    f.write(content)
            gpt = GPT(current_user.API_Key)
            attribute["MachineDescription"] = gpt.generate_database_description(cols_info)
            attribute["SavePath"] = save_path+"/database.db"
            attribute.update({"SavePath": save_path+"/database.db"})
            attribute.pop("url")
        else:
            #handle url
            SavePath = str(attribute.get("url"))
            connection = sqlite3.connect(SavePath)
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            cols_info = {}
            for table in tables:
                columns = list(pd.read_sql(f"SELECT * FROM {table[0]}", connection).columns)
                cols_info[table[0]] = columns
            gpt = GPT(current_user.API_Key)
            attribute["MachineDescription"] = gpt.generate_database_description(cols_info)
            attribute.update({"SavePath": SavePath})
            attribute.pop("url")
            machine_des = ''
            attribute.update({"MachineDescription": machine_des})
        db_database = models.Database(**attribute)
        db.add(db_database)
        db.commit()
        db.refresh(db_database)
        return get_databases(db, current_user)
    except SQLAlchemyError as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.rollback()
        raise HTTPException(status_code=400, detail="An error occurred while creating the database: " + str(e))

@router.post("/update", response_model=schemas.Database)
def update_database(database: schemas.Database, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        db_database = db.query(models.Database).filter(models.Database.DatabaseID == database.DatabaseID).first()
        if not db_database:
            raise HTTPException(status_code=404, detail="Database not found")
        for key, value in database.model_dump(exclude_unset=True).items():
            setattr(db_database, key, value)
        db.commit()
        db.refresh(db_database)
        
        return db_database
    except SQLAlchemyError as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.rollback()
        raise HTTPException(status_code=400, detail="An error occurred while updating the database: " + str(e))
@router.post("/get_by_uid", response_model=List[schemas.Database])
def get_databases(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user_id = current_user.UserID
    databases = db.query(models.Database).filter(models.Database.UserID == user_id).order_by(desc(models.Database.CreatedDate)).all()
    return databases

@router.post("/delete", response_model=List[schemas.Database])
def delete_database(database: schemas.DatabaseDelete, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    try:
        #delete all conversation with this database

        conversations_to_delete = db.query(models.Conversation).filter(models.Conversation.DatabaseID == database.DatabaseID).all()
        # print(conversations_to_delete)
        for conversation in conversations_to_delete:
            # print(conversation)
            delete_conversation(conversation, db, current_user)
        db.commit()
        db_database = db.query(models.Database).filter(models.Database.DatabaseID == database.DatabaseID).first()
        if not db_database:
            raise HTTPException(status_code=404, detail="Database not found")
        # save_path = db_database.SavePath
        # dir_to_delete = save_path.replace("database.db", "")
        # print("Delete Folder: ",dir_to_delete)
        # if os.path.exists(dir_to_delete):
        #         shutil.rmtree(dir_to_delete)
        db.delete(db_database)
        db.commit()
        return get_databases(db, current_user)
    except SQLAlchemyError as e:
        # Rollback transaction nếu có lỗi xảy ra
        db.rollback()
        raise HTTPException(status_code=400, detail="An error occurred while deleting the database: " + str(e))