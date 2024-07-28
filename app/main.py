from fastapi import FastAPI
from app.routers import auth, conversations, messages, databases
from app.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

# Cấu hình CORS
origins = [
    "http://localhost:3000",
    # Thêm các nguồn khác nếu cần thiết
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo cơ sở dữ liệu
Base.metadata.create_all(bind=engine)

# Đăng ký các router
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(databases.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI ChatApp!"}
