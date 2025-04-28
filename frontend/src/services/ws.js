let sockets = {};
let listeners = {};

export const connectWS = (url) => {
    if (sockets[url]) {
        console.warn('Websocket ya está conectado a la URL:', url);
        return;
    }

    const socket = new WebSocket(url);
    sockets[url] = socket;
    listeners[url] = [];

    socket.onopen = () => {
        console.log('✅ Conexión WebSocket establecida.');
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        listeners[url].forEach(listener => listener(data));
    };

    socket.onclose = () => {
        console.warn('⚠️ Conexión WebSocket cerrada:', event.reason);
        // socket = null;
        delete sockets[url];
        delete listeners[url];
        // // Reintentar la conexión después de un tiempo
        // setTimeout(() => {
        //     console.log('🔄 Reitentando conexion al Websocket...');
        //     connectWS(url);
        // }, 5000)
    };

    socket.onerror = (error) => {
        console.error(`❌ Error en WebSocket ${url}:`, error);
    };
}

// Funcion para cerrar la conexion al websocket
export const closeWS = () => {
    if (sockets[url]) {
        sockets[url].close();
        // socket = null;
        delete sockets[url];
        delete listeners[url];
    } else {
        console.warn(`WebSocket no está conectado para ${url}.`);
    }
}

// Funcion para enviar un mensaje al websocket
export const sendMessageToWS = (url, message) => {
    if (sockets[url] && sockets[url].readyState === WebSocket.OPEN) {
        sockets[url].send(JSON.stringify(message));
    } else {
        console.warn(`⚠️ No se puede enviar el mensaje. WebSocket no está conectado para ${url}`);
    }
}

export const suscribeToWS = (url, callback) => {
    // if (socket) {
    //     listeners.push(callback);
    // }
    if (!listeners[url]) listeners[url] = [];
    listeners[url].push(callback);
}

export const unsubscribeFromWS = (url, callback) => {
    // if (socket) {
    //     listeners = listeners.filter(listener => listener !== callback);
    // }
    if (listeners[url]) {
        listeners[url] = listeners[url].filter(listener => listener !== callback);
    }
}