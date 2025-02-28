# app.py
import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Time, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
from dotenv import load_dotenv
import pytz
from datetime import datetime, time
from typing import Optional
import enum

load_dotenv()

app = FastAPI()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Database Models ---
class UserRole(enum.Enum):
    DEFAULT = "default"
    DEVELOPER = "developer"
    CUSTOMER = "customer"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    timezone = Column(String(50), nullable=True)
    working_hours_start = Column(Time, nullable=True)
    working_hours_end = Column(Time, nullable=True)
    is_admin = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.DEFAULT) # Added user role

class ChatRoom(Base):
    __tablename__ = 'chat_rooms'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    chat_room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    text = Column(Text)
    file_id = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    user = relationship("User")
    chat_room = relationship("ChatRoom")

class UserChatRoom(Base):
    __tablename__ = 'user_chat_rooms'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    chat_room_id = Column(Integer, ForeignKey('chat_rooms.id'), primary_key=True)

Base.metadata.create_all(bind=engine)

# --- Pydantic Models for Request/Response Validation ---
class UserCreate(BaseModel):
    telegram_id: int
    display_name: str
    timezone: Optional[str] = None
    working_hours_start: Optional[str] = None  # Store as string for simplicity
    working_hours_end: Optional[str] = None  # Store as string for simplicity
    role: Optional[str] = None

class ChatRoomCreate(BaseModel):
    name: str

class ChatRoomResponse(BaseModel):
    id: int
    name: str

class MessageCreate(BaseModel):
    chat_room_id: int
    user_id: int
    text: str
    file_id: Optional[str] = None
    file_type: Optional[str] = None

class UserResponse(BaseModel):
    telegram_id: int
    display_name: str
    timezone: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    role: str

# --- API Endpoints ---
@app.post("/api/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_or_update_user(user: UserCreate, db: Session = Depends(get_db)):
    """Creates or updates a user with timezone and working hours."""
    db_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()

    if db_user:
        # Update existing user
        db_user.display_name = user.display_name
        if user.timezone:
            try:
                pytz.timezone(user.timezone)
                db_user.timezone = user.timezone
            except pytz.exceptions.UnknownTimeZoneError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timezone")

        if user.working_hours_start:
            try:
                datetime.strptime(user.working_hours_start, "%H:%M").time()
                db_user.working_hours_start = datetime.strptime(user.working_hours_start, "%H:%M").time()
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid working hours start format")

        if user.working_hours_end:
            try:
                datetime.strptime(user.working_hours_end, "%H:%M").time()
                db_user.working_hours_end = datetime.strptime(user.working_hours_end, "%H:%M").time()
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid working hours end format")

        if user.role:
            try:
                db_user.role = UserRole[user.role.upper()]
            except KeyError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user role")

        db.commit()
        db.refresh(db_user)
        return db_user
    else:
        # Create new user
        try:
            role = UserRole.DEFAULT
            if user.role:
                try:
                    role = UserRole[user.role.upper()]
                except KeyError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user role")

            new_user = User(
                telegram_id=user.telegram_id,
                display_name=user.display_name,
                timezone=user.timezone,
                working_hours_start=datetime.strptime(user.working_hours_start, "%H:%M").time() if user.working_hours_start else None,
                working_hours_end=datetime.strptime(user.working_hours_end, "%H:%M").time() if user.working_hours_end else None,
                role=role
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        except pytz.exceptions.UnknownTimeZoneError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid timezone")
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid data format: {e}")

@app.get("/api/rooms", response_model=list[ChatRoomResponse])
async def list_rooms(db: Session = Depends(get_db)):
    """Lists all chat rooms."""
    rooms = db.query(ChatRoom).all()
    return rooms

@app.post("/api/rooms", status_code=status.HTTP_201_CREATED, response_model=ChatRoomResponse)
async def create_room(room: ChatRoomCreate, creator_id: int, db: Session = Depends(get_db)):
    """Creates a new chat room."""
    db_room = ChatRoom(name=room.name, creator_id=creator_id)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@app.get("/api/users/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Retrieves user data by Telegram ID."""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )
