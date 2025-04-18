let socket = null;
let listeners = [];

export const connectWS = (url) => {
    if (socket) {
        console.warn('Websocket ya está conectado. No se puede volver a conectar.');
        return;
    }

    socket = new WebSocket(url);

    socket.onopen = () => {
        console.log('✅ Conexión WebSocket establecida.');
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        listeners.forEach(listener => listener(data));
    };

    socket.onclose = () => {
        console.warn('⚠️ Conexión WebSocket cerrada:', event.reason);
        socket = null;
        setTimeout(() => {
            console.log('🔄 Reitentando conexion al Websocket...');
            connectWS(url);
        }, 5000)
        
    };

    socket.onerror = (error) => {
        console.error('❌ Error en WebSocket:', error);
    };
}

// Funcion para cerrar la conexion al websocket
export const closeWS = () => {
    if (socket) {
        socket.close();
        socket = null;
    } else {
        console.warn('WebSocket no está conectado. No se puede cerrar.');
    }
}

// Funcion para enviar un mensaje al websocket
export const sendMessageToWS = (message) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(message));
    } else {
        console.warn('⚠️ No se puede enviar el mensaje. WebSocket no está conectado.');
    }
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