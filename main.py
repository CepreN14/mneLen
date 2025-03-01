from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from database import engine, rooms, messages
from sqlalchemy.sql import select, insert

app = FastAPI()

# Модели данных
class Room(BaseModel):
    id: int
    name: str

class Message(BaseModel):
    id: int
    room_id: int
    sender: str
    text: str

# Эндпоинт для получения списка комнат
@app.get("/api/rooms", response_model=List[Room])
async def get_rooms():
    query = select(rooms)
    async with engine.connect() as connection:
        result = await connection.execute(query)
        return [Room(id=row.id, name=row.name) for row in result]

# Эндпоинт для создания новой комнаты
@app.post("/api/rooms", response_model=Room)
async def create_room(name: str):
    query = insert(rooms).values(name=name)
    async with engine.connect() as connection:
        result = await connection.execute(query)
        await connection.commit()
        return Room(id=result.lastrowid, name=name)

# Эндпоинт для получения сообщений в комнате
@app.get("/api/messages", response_model=List[Message])
async def get_messages(room_id: int):
    query = select(messages).where(messages.c.room_id == room_id)
    async with engine.connect() as connection:
        result = await connection.execute(query)
        return [Message(id=row.id, room_id=row.room_id, sender=row.sender, text=row.text) for row in result]

# Эндпоинт для отправки сообщения в комнату
@app.post("/api/messages", response_model=Message)
async def send_message(room_id: int, sender: str, text: str):
    query = insert(messages).values(room_id=room_id, sender=sender, text=text)
    async with engine.connect() as connection:
        result = await connection.execute(query)
        await connection.commit()
        return Message(id=result.lastrowid, room_id=room_id, sender=sender, text=text)
