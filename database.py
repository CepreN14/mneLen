from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

# Подключение к SQLite
DATABASE_URL = "sqlite:///./test.db"

# Создание движка SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()

# Определение таблиц
rooms = Table(
    "rooms",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, unique=True, index=True),
)

messages = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("room_id", Integer, index=True),
    Column("sender", String, index=True),
    Column("text", String),
)

# Создание таблиц в базе данных
metadata.create_all(bind=engine)
