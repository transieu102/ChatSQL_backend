from pydantic import BaseModel, HttpUrl, model_validator, Field
from fastapi import UploadFile
from typing import List, Optional
from datetime import datetime

class UserRequest(BaseModel):
    UserID: int
    API_Key: str

class UserCreate(BaseModel):
    Username: str
    Password: str

class User(BaseModel):
    UserID: int
    Username: str
    API_Key: Optional[str] = None

    class Config:
        from_attributes = True
class LoginResponse(BaseModel):
    # {"status": "success", "user_info": db_user}
    status: str
    user_info: User

class DatabaseCreate(BaseModel):
    DataName: str
    UserDescription: Optional[str] = None
    UserID: int
    url: Optional[HttpUrl] = None
    # @model_validator(mode='before')
    # def check_url_or_files(cls, values):
    #     url = values.get('url')
    #     files = values.get('files')
    #     if files
    #     if not url and not files:
    #         raise ValueError('Either url or files must be provided')
    #     return values



class Database(BaseModel):
    DatabaseID: int
    DataName: str
    SavePath: str
    MachineDescription: str
    UserDescription: Optional[str]
    CreatedDate: Optional[datetime] = Field(default_factory=datetime.now)
    UserID: int
    
    class Config:
        from_attributes = True

class DatabaseDelete(BaseModel):
    DatabaseID: int

class ConversationCreate(BaseModel):
    DatabaseID: int
    UserID: int
    ConversationName: Optional[str]
class ConversationID(BaseModel):
    ConversationID: int
class Conversation(BaseModel):
    ConversationID: int
    ConversationName: str
    LastModifyDate: Optional[datetime] = Field(default_factory=datetime.now)
    DatabaseID: int
    UserID: int
    
    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    Content: str
    Role: str
    ConversationID: int
    Index: int

class Message(BaseModel):
    MessageID: int
    ConversationID: int
    Content: str
    Role: str
    Index : int
    
    class Config:
        from_attributes = True
