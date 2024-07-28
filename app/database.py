# from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint, CheckConstraint
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker, relationship
# from config import Config

# Base = declarative_base()

# # Định nghĩa các bảng như các class model với ràng buộc toàn vẹn dữ liệu
# class User(Base):
#     __tablename__ = 'User'
#     UserID = Column(Integer, primary_key=True)
#     Username = Column(String, unique=True, nullable=False)
#     Password = Column(String, nullable=False)
#     API_Key = Column(String, unique=True, nullable=False)

# class Database(Base):
#     __tablename__ = 'Database'
#     DatabaseID = Column(Integer, primary_key=True)
#     DataName = Column(String, nullable=False)
#     SavePath = Column(String, nullable=False)
#     MachineDescription = Column(String, nullable=False)
#     UserDescription = Column(String, nullable=False)
#     UserID = Column(Integer, ForeignKey('User.UserID', ondelete='CASCADE'), nullable=False)
#     user = relationship("User")

# class Conversation(Base):
#     __tablename__ = 'Conversation'
#     ConversationID = Column(Integer, primary_key=True)
#     ConversationName = Column(String, nullable=False)
#     DatabaseID = Column(Integer, ForeignKey('Database.DatabaseID', ondelete='CASCADE'), nullable=False)
#     database = relationship("Database")

# class Message(Base):
#     __tablename__ = 'Message'
#     MessageID = Column(Integer, primary_key=True)
#     ConversationID = Column(Integer, ForeignKey('Conversation.ConversationID', ondelete='CASCADE'), nullable=False)
#     Content = Column(String, nullable=False)
#     Role = Column(String, nullable=False)
#     conversation = relationship("Conversation")

# # Khởi tạo engine và session
# engine = create_engine('sqlite:///'+Config['database_path'])
# Session = sessionmaker(bind=engine)

# # Hàm tạo cơ sở dữ liệu
# def create_database():
#     Base.metadata.create_all(engine)

# # Lớp điều khiển dữ liệu sử dụng SQLAlchemy
# class DataControler:
#     def __init__(self):
#         self.session = Session()

#     # USER
#     def insertUser(self, username, password, api_key):
#         user = User(Username=username, Password=password, API_Key=api_key)
#         self.session.add(user)
#         self.session.commit()
#         return user.UserID

#     def updateUser(self, user_id, username, password, api_key):
#         user = self.session.query(User).filter_by(UserID=user_id).first()
#         if user:
#             user.Username = username
#             user.Password = password
#             user.API_Key = api_key
#             self.session.commit()

#     def loginUser(self, username, password):
#         user = self.session.query(User).filter_by(Username=username, Password=password).first()
#         if user:
#             return user.UserID
#         return None

#     # DATABASE
#     def insertDatabase(self, data_name, save_path, machine_description, user_description, user_id):
#         database = Database(
#             DataName=data_name,
#             SavePath=save_path,
#             MachineDescription=machine_description,
#             UserDescription=user_description,
#             UserID=user_id
#         )
#         self.session.add(database)
#         self.session.commit()
#         return database.DatabaseID

#     def updateDatabase(self, database_id, data_name, save_path, machine_description, user_description):
#         database = self.session.query(Database).filter_by(DatabaseID=database_id).first()
#         if database:
#             database.DataName = data_name
#             database.SavePath = save_path
#             database.MachineDescription = machine_description
#             database.UserDescription = user_description
#             self.session.commit()

#     def getDatabases(self, user_id):
#         databases = self.session.query(Database).filter_by(UserID=user_id).all()
#         return [{
#             'database_id': db.DatabaseID,
#             'data_name': db.DataName,
#             'save_path': db.SavePath,
#             'machine_description': db.MachineDescription,
#             'user_description': db.UserDescription
#         } for db in databases]

#     # CONVERSATION
#     def insertConversation(self, conversation_name, database_id, user_id):
#         conversation = Conversation(
#             ConversationName=conversation_name,
#             DatabaseID=database_id
#         )
#         self.session.add(conversation)
#         self.session.commit()
#         return conversation.ConversationID

#     def updateConversation(self, conversation_id, conversation_name):
#         conversation = self.session.query(Conversation).filter_by(ConversationID=conversation_id).first()
#         if conversation:
#             conversation.ConversationName = conversation_name
#             self.session.commit()

#     def getConversations(self, user_id):
#         conversations = self.session.query(Conversation).filter_by(DatabaseID=user_id).all()
#         return [{
#             'conversation_id': conv.ConversationID,
#             'conversation_name': conv.ConversationName,
#             'database_id': conv.DatabaseID
#         } for conv in conversations]

#     # MESSAGE
#     def insertMessage(self, conversation_id, content, role):
#         message = Message(
#             ConversationID=conversation_id,
#             Content=content,
#             Role=role
#         )
#         self.session.add(message)
#         self.session.commit()
#         return message.MessageID

#     def updateMessage(self, message_id, content, role):
#         message = self.session.query(Message).filter_by(MessageID=message_id).first()
#         if message:
#             message.Content = content
#             message.Role = role
#             self.session.commit()

#     def getMessages(self, conversation_id):
#         messages = self.session.query(Message).filter_by(ConversationID=conversation_id).all()
#         return [{
#             'content': msg.Content,
#             'role': msg.Role
#         } for msg in messages]

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./chatapp.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
