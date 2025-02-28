// web_app/script.js
Telegram.WebApp.ready();

const app = {
    rooms: [],
    userId: null,
    init: async function() {
        if (Telegram.WebApp.initDataUnsafe && Telegram.WebApp.initDataUnsafe.user) {
            this.userId = Telegram.WebApp.initDataUnsafe.user.id; // Получить ID пользователя
            console.log("ID пользователя:", this.userId);
        } else {
            this.userId = 'unknown'; // Обработка случая, когда информация о пользователе недоступна
            console.warn("ID пользователя недоступен. Проверьте настройки Telegram Web App SDK.")
        }
        await this.fetchRooms();
        this.renderRooms();
    },
    fetchRooms: async function() {
        try {
            const response = await fetch('/api/rooms');
            if (!response.ok) {
                throw new Error(`Ошибка HTTP! Статус: ${response.status}`);
            }
            const data = await response.json();
            this.rooms = data.rooms;
        } catch (error) {
            console.error("Ошибка при получении списка комнат:", error);
            alert("Ошибка при получении списка комнат. Проверьте консоль для подробностей."); // Предоставить пользователю обратную связь
        }
    },
    renderRooms: function() {
        const roomsDiv = document.getElementById('rooms');
        roomsDiv.innerHTML = ''; // Очистить существующий контент
        if (this.rooms.length === 0) {
            roomsDiv.textContent = "Нет доступных комнат.";
            return;
        }
        this.rooms.forEach(room => {
            const roomDiv = document.createElement('div');
            roomDiv.classList.add('room');
            roomDiv.textContent = room.name;
            roomsDiv.appendChild(roomDiv);
        });
    }
};

app.init();
