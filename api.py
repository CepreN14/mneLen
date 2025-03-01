from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешить запросы с других доменов

# Хранение данных (в реальном проекте используйте базу данных)
rooms = []
messages = []

@app.route("/api/add_room", methods=["POST"])
def add_room():
    data = request.json
    room_name = data.get("room_name")
    if room_name:
        rooms.append(room_name)
        return jsonify({"status": "success", "message": f"Комната '{room_name}' создана."})
    return jsonify({"status": "error", "message": "Неверные данные."})

@app.route("/api/send_message", methods=["POST"])
def send_message():
    data = request.json
    room_name = data.get("room_name")
    sender = data.get("sender")
    message = data.get("message")
    if room_name and sender and message:
        messages.append({"room_name": room_name, "sender": sender, "message": message})
        return jsonify({"status": "success", "message": "Сообщение отправлено."})
    return jsonify({"status": "error", "message": "Неверные данные."})

@app.route("/api/get_data", methods=["GET"])
def get_data():
    return jsonify({"rooms": rooms, "messages": messages})

if __name__ == "__main__":
    app.run(debug=True)