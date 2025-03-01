# app.py
import os
from enum import Enum
from datetime import datetime, time
import logging
import uuid
import pytz
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy import Enum as SQLEnum
from flask_cors import CORS

load_dotenv()

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///./app.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)  # Enable CORS for all routes


class UserRole(Enum):
    DEFAULT = "default"
    DEVELOPER = "developer"
    CUSTOMER = "customer"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=str(uuid.uuid4()))
    telegram_id = db.Column(db.Integer, unique=True)
    display_name = db.Column(db.String(200))
    timezone = db.Column(db.String(100), nullable=True)
    working_hours_start = db.Column(db.Time, nullable=True)
    working_hours_end = db.Column(db.Time, nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.DEFAULT)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'public_id': self.public_id,
            'telegram_id': self.telegram_id,
            'display_name': self.display_name,
            'timezone': self.timezone,
            'working_hours_start': str(self.working_hours_start),
            'working_hours_end': str(self.working_hours_end),
            'role': self.role.value,
            'created_at': str(self.created_at)
        }

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer)
    name = db.Column(db.String(200))

with app.app_context():
    db.create_all()

@app.route('/api/users', methods=['POST'])
def create_or_update_user():
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    display_name = data.get('display_name')
    timezone = data.get('timezone')
    working_hours_start = data.get('working_hours_start')
    working_hours_end = data.get('working_hours_end')
    role = data.get('role')

    user = User.query.filter_by(telegram_id=telegram_id).first()

    if user:
        # Update existing user
        user.display_name = display_name or user.display_name
        user.timezone = timezone or user.timezone

        try:
            if working_hours_start:
                time_object = datetime.strptime(working_hours_start, '%H:%M').time()
                user.working_hours_start = time_object
            if working_hours_end:
                time_object = datetime.strptime(working_hours_end, '%H:%M').time()
                user.working_hours_end = time_object
        except ValueError:
            return jsonify({'message': 'Invalid time format. Use HH:MM'}), 400

        try:
            if role:
                user.role = UserRole[role.upper()]
        except KeyError:
            return jsonify({'message': 'Invalid user role'}), 400

        db.session.commit()
        logging.info(f"User updated: {user.to_dict()}")
        return jsonify(user.to_dict()), 200
    else:
        # Create new user
        try:
            new_user = User(
                telegram_id=telegram_id,
                display_name=display_name,
                timezone=timezone,
                working_hours_start=datetime.strptime(working_hours_start, '%H:%M').time() if working_hours_start else None,
                working_hours_end=datetime.strptime(working_hours_end, '%H:%M').time() if working_hours_end else None,
                role=UserRole[role.upper()] if role else UserRole.DEFAULT
            )
        except ValueError as e:
            if "Invalid time format" in str(e):
                return jsonify({'message': 'Invalid time format. Use HH:MM'}), 400
            elif "object is not callable" in str(e):
                 new_user = User(
                    telegram_id=telegram_id,
                    display_name=display_name,
                    timezone=timezone,
                    working_hours_start=datetime.strptime(working_hours_start, '%H:%M').time() if working_hours_start else None,
                    working_hours_end=datetime.strptime(working_hours_end, '%H:%M').time() if working_hours_end else None,
                    role=UserRole[role.upper()] if role else UserRole.DEFAULT
                )
            else:
                return jsonify({'message': str(e)}), 400
        except KeyError:
            return jsonify({'message': 'Invalid user role'}), 400

        db.session.add(new_user)
        db.session.commit()
        logging.info(f"User created: {new_user.to_dict()}")
        return jsonify(new_user.to_dict()), 201

@app.route('/api/users/<int:telegram_id>', methods=['GET'])
def get_user(telegram_id):
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if user:
        return jsonify(user.to_dict()), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/api/rooms', methods=['POST'])
def create_room():
    data = request.get_json()
    creator_id = data.get('creator_id')
    name = data.get('name')

    new_room = ChatRoom(creator_id=creator_id, name=name)
    db.session.add(new_room)
    db.session.commit()
    return jsonify({'id': new_room.id, 'creator_id': new_room.creator_id, 'name': new_room.name}), 201

@app.route('/api/rooms', methods=['GET'])
def list_rooms():
    rooms = ChatRoom.query.all()
    return jsonify([{'id': room.id, 'creator_id': room.creator_id, 'name': room.name} for room in rooms]), 200

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000) #port = 5000
