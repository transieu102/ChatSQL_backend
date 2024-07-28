from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = 'User'
    UserID = Column(Integer, primary_key=True)
    Username = Column(String, unique=True, nullable=False)
    Password = Column(String, nullable=False)
    API_Key = Column(String, unique=False, nullable=True)

class Database(Base):
    __tablename__ = 'Database'
    DatabaseID = Column(Integer, primary_key=True)
    DataName = Column(String, nullable=False)
    SavePath = Column(String, nullable=False)
    MachineDescription = Column(String, nullable=False)
    UserDescription = Column(String, nullable=True)
    CreatedDate = Column(DateTime, default=datetime.now)
    UserID = Column(Integer, ForeignKey('User.UserID', ondelete='CASCADE'), nullable=False)
    user = relationship("User")

class Conversation(Base):
    __tablename__ = 'Conversation'
    ConversationID = Column(Integer, primary_key=True)
    ConversationName = Column(String, nullable=False)
    UserID = Column(Integer, ForeignKey('User.UserID', ondelete='CASCADE'), nullable=False)
    user = relationship("User")
    DatabaseID = Column(Integer, ForeignKey('Database.DatabaseID', ondelete='CASCADE'), nullable=False)
    database = relationship("Database")
    LastModified = Column(DateTime, default=datetime.now, nullable= True)

class Message(Base):
    __tablename__ = 'Message'
    MessageID = Column(Integer, primary_key=True)
    Index = Column(Integer, nullable=False)
    ConversationID = Column(Integer, ForeignKey('Conversation.ConversationID', ondelete='CASCADE'), nullable=False)
    Content = Column(String, nullable=False)
    Role = Column(String, nullable=False)
    conversation = relationship("Conversation")

User.databases = relationship("Database", order_by=Database.DatabaseID, back_populates="user")
Database.conversations = relationship("Conversation", order_by=Conversation.ConversationID, back_populates="database")
Conversation.messages = relationship("Message", order_by=Message.MessageID, back_populates="conversation")
