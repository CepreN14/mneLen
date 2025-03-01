from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Модели данных
class Room(BaseModel):
    id: str
    name: str

class Message(BaseModel):
    id: str
    room_id: str
    sender: str
    text: str

# Хранение данных (в реальном проекте используйте базу данных)
rooms = []
messages = []

# Эндпоинт для получения списка комнат
@app.get("/api/rooms", response_model=List[Room])
def get_rooms():
    return rooms

# Эндпоинт для создания новой комнаты
@app.post("/api/rooms", response_model=Room)
def create_room(name: str):
    new_room = Room(id=str(len(rooms) + 1), name=name)
    rooms.append(new_room)
    return new_room

# Эндпоинт для получения сообщений в комнате
@app.get("/api/messages", response_model=List[Message])
def get_messages(room_id: str):
    room_messages = [msg for msg in messages if msg.room_id == room_id]
    return room_messages

# Эндпоинт для отправки сообщения в комнату
@app.post("/api/messages", response_model=Message)
def send_message(room_id: str, sender: str, text: str):
    new_message = Message(
        id=str(len(messages) + 1),
        room_id=room_id,
        sender=sender,
        text=text
    )
    messages.append(new_message)
    return new_message
