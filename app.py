# app.py (Часть с базой данных)
import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Time, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///./app.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Database Models (Simplified - adapt as needed)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    working_hours_start = Column(Time, nullable=True)
    working_hours_end = Column(Time, nullable=True)
    is_admin = Column(Boolean, default=False)

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

with app.app_context():
    Base.metadata.create_all(bind=db.engine)

def get_db():
    db_session = Session(db.engine)
    try:
        yield db_session
    finally:
        db_session.close()

# API Endpoints (Examples)
@app.route('/api/rooms', methods=['GET'])
def list_rooms():
    db: Session = next(get_db())
    rooms = db.query(ChatRoom).all()
    room_list = [{"id": room.id, "name": room.name} for room in rooms]
    return jsonify(rooms=room_list)

@app.route('/api/messages', methods=['POST'])
def create_message():
    data = request.get_json()
    user_id = data.get('user_id')
    chat_room_id = data.get('chat_room_id')
    text = data.get('text')

    if not all([user_id, chat_room_id, text]):
        return jsonify({"error": "Missing data"}), 400

    db: Session = next(get_db())
    message = Message(user_id=user_id, chat_room_id=chat_room_id, text=text)
    db.add(message)
    db.commit()
    return jsonify({"message": "Message created"}), 201

# Authentication (Simplified - Replace with proper auth)
def authenticate_user(telegram_id):
    db: Session = next(get_db())
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        #Create a new user
        user = User(telegram_id=telegram_id, display_name="New User") # Todo: Replace hardcode
        db.add(user)
        db.commit()
    return user