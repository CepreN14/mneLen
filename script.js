// web_app/script.js
Telegram.WebApp.ready();

const app = {
    rooms: [],
    userId: null,
    init: async function() {
        this.userId = Telegram.WebApp.initDataUnsafe.user.id; // Get user ID
        await this.fetchRooms();
        this.renderRooms();
    },
    fetchRooms: async function() {
        const response = await fetch('https://cepren14.github.io/mneLen/api/rooms'); //TODO: Replace
        this.rooms = await response.json();
    },
    renderRooms: function() {
        const roomsDiv = document.getElementById('rooms');
        this.rooms.rooms.forEach(room => {
            const roomDiv = document.createElement('div');
            roomDiv.classList.add('room');
            roomDiv.textContent = room.name;
            roomsDiv.appendChild(roomDiv);
        });
    }
};

app.init();
