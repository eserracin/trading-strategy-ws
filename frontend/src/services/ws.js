// src/services/ws.js
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
        let data
        try {
            if (!event.data) throw new Error("Mensaje vacío");
            data = JSON.parse(event.data);
        } catch (error) {
            console.error('❌ Error al parsear el mensaje del WebSocket:', error);
            return;
        }
        if (Array.isArray(listeners[url])) {
            listeners[url].forEach(listener => listener(data));
        }
    };

    socket.onclose = (event) => {
        if (Array.isArray(listeners[url])) {
            listeners[url].forEach(listener =>
              listener({ tipo: 'closed', reason: event.reason })
            );
          }
        console.warn('⚠️ Conexión WebSocket cerrada:', event.reason);
        delete sockets[url];
        delete listeners[url];
    };

    socket.onerror = (error) => {
        console.error(`❌ Error en WebSocket ${url}:`, error);
    };
}

// Funcion para cerrar la conexion al websocket
export const closeWS = (url) => {
    if (sockets[url]) {
        sockets[url].close();
        delete sockets[url];
        delete listeners[url];
    } else {
        console.warn(`WebSocket no está conectado para ${url}.`);
    }
    if (listeners[url]) {
        delete listeners[url];
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
    if (!listeners[url]) listeners[url] = [];
    
    if (!listeners[url].includes(callback)) {
        listeners[url].push(callback);
    }
    
}

export const unsubscribeFromWS = (url, callback) => {
    if (listeners[url]) {
        listeners[url] = listeners[url].filter(listener => listener !== callback);
        // Si ya no hay listeners, cerramos la conexion
        if (listeners[url].length === 0) {
            closeWS(url);
        }
    }
}