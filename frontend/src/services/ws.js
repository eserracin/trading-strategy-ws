let socket = null;
let listeners = [];

export const connectWS = (url) => {
    if (socket) {
        return;
    }

    socket = new WebSocket(url);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        listeners.forEach(listener => {
            listener(data);
        });
    };

    socket.onclose = () => {
        console.warn('Disconnected from the server');
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

export const suscribeToWS = (callback) => {
    if (socket) {
        listeners.push(callback);
    }
}

export const unsubscribeFromWS = (callback) => {
    if (socket) {
        listeners = listeners.filter(listener => listener !== callback);
    }
}