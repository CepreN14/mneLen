# app.py (Flask Backend)
import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Time, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv
import pytz

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///./app.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Модели базы данных
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    timezone = Column(String(50), nullable=True)
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

# API Endpoints (Примеры)
@app.route('/api/rooms', methods=['GET'])
def list_rooms():
    with app.app_context():
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
        return jsonify({"error": "Отсутствуют необходимые данные"}), 400

    with app.app_context():
        db: Session = next(get_db())
        message = Message(user_id=user_id, chat_room_id=chat_room_id, text=text)
        db.add(message)
        db.commit()
    return jsonify({"message": "Сообщение создано"}), 201

@app.route('/api/users', methods=['POST'])
def create_or_update_user():
    """Создает или обновляет пользователя с часовым поясом и рабочим временем."""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    display_name = data.get('display_name')
    timezone_str = data.get('timezone')
    working_hours_start_str = data.get('working_hours_start')
    working_hours_end_str = data.get('working_hours_end')

    if not all([telegram_id, display_name]):
        return jsonify({"error": "Отсутствуют необходимые данные"}), 400

    with app.app_context():
        db: Session = next(get_db())
        user = db.query(User).filter_by(telegram_id=telegram_id).first()

        if user:
            # Обновить существующего пользователя
            user.display_name = display_name
            if timezone_str:
                try:
                    pytz.timezone(timezone_str)  # Проверить часовой пояс
                    user.timezone = timezone_str
                except pytz.exceptions.UnknownTimeZoneError:
                    return jsonify({"error": "Неверный часовой пояс"}), 400
            if working_hours_start_str:
                try:
                    user.working_hours_start = datetime.strptime(working_hours_start_str, "%H:%M").time()
                except ValueError:
                    return jsonify({"error": "Неверный формат времени начала работы"}), 400
            if working_hours_end_str:
                try:
                    user.working_hours_end = datetime.strptime(working_hours_end_str, "%H:%M").time()
                except ValueError:
                    return jsonify({"error": "Неверный формат времени окончания работы"}), 400
            db.commit()
            return jsonify({"message": "Пользователь успешно обновлен"}), 200
        else:
            # Создать нового пользователя
            try:
                user = User(telegram_id=telegram_id, display_name=display_name)
                if timezone_str:
                    try:
                        pytz.timezone(timezone_str) # Проверить часовой пояс
                        user.timezone = timezone_str
                    except pytz.exceptions.UnknownTimeZoneError:
                        return jsonify({"error": "Неверный часовой пояс"}), 400
                if working_hours_start_str:
                    try:
                        user.working_hours_start = datetime.strptime(working_hours_start_str, "%H:%M").time()
                    except ValueError:
                        return jsonify({"error": "Неверный формат времени начала работы"}), 400
                if working_hours_end_str:
                    try:
                        user.working_hours_end = datetime.strptime(working_hours_end_str, "%H:%M").time()
                    except ValueError:
                        return jsonify({"error": "Неверный формат времени окончания работы"}), 400
                db.add(user)
                db.commit()
                return jsonify({"message": "Пользователь успешно создан"}), 201
            except Exception as e:
                logging.error(f"Ошибка при создании/обновлении пользователя: {e}")
                return jsonify({"error": f"Ошибка при создании/обновлении пользователя: {e}"}), 500

def authenticate_user(telegram_id):
    """Аутентифицирует пользователя, создает нового пользователя, если не существует."""
    with app.app_context():
        db: Session = next(get_db())
        user = db.query(User).filter_by(telegram_id=telegram_id).first()
        return user

def create_room_api(creator_id, room_name):
    with app.app_context():
        db: Session = next(get_db())
        # Check if a room with this name already exists.
        if db.query(ChatRoom).filter_by(name=room_name).first():
            raise ValueError(f"Комната с именем '{room_name}' уже существует.")

        room = ChatRoom(name=room_name, creator_id=creator_id)
        db.add(room)
        db.commit()

        # Также добавить создателя в комнату
        user_chat_room = UserChatRoom(user_id=creator_id, chat_room_id=room.id)
        db.add(user_chat_room)
        db.commit()
        return room

def add_user_to_room_api(user_name, room_name):
    with app.app_context():
        db: Session = next(get_db())

        user = db.query(User).filter_by(display_name=user_name).first()
        if not user:
            raise ValueError(f"Пользователь с именем '{user_name}' не найден.")

        room = db.query(ChatRoom).filter_by(name=room_name).first()
        if not room:
            raise ValueError(f"Комната с именем '{room_name}' не найдена.")

        # Check if user is already in the room
        if db.query(UserChatRoom).filter_by(user_id=user.id, chat_room_id=room.id).first():
            raise ValueError(f"Пользователь '{user_name}' уже состоит в комнате '{room_name}'.")

        user_chat_room = UserChatRoom(user_id=user.id, chat_room_id=room.id)
        db.add(user_chat_room)
        db.commit()

def list_rooms_api(user_id):
    with app.app_context():
        db: Session = next(get_db())
        user_rooms = db.query(ChatRoom).join(UserChatRoom).filter(UserChatRoom.user_id == user_id).all()
        return [{"id": room.id, "name": room.name} for room in user_rooms]

if __name__ == '__main__':
    logging.info("Запуск Flask приложения")
    app.run(debug=True)
