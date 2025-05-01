import { useEffect, useCallback, useRef } from "react";
import { connectWS, suscribeToWS, unsubscribeFromWS, closeWS } from "../services/ws";

/**
 * Suscribe a un stream de velas ("candles") para la clave dada y
 * ejecuta onData cada vez que llega un mensaje.
 *
 * @param {string} key        - Formato "SYMBOL::STRATEGY::TF"
 * @param {(data: any) => void} onData
 */
export const useCandleStream = (key, onData) => {
    // Manteng la ultima referencia de callback sin disparar re-suscripciones
    const onDataRef = useRef(onData);
    onDataRef.current = onData;

    // Memoriza la url para que cambie solo cuando cambie la clave
    const url = key ? `${import.meta.env.VITE_WS_URL}/candle-stream/${encodeURIComponent(key)}` : null;

    useEffect(() => {
        if (!url) return;

        // Handler interno que delega en la ref actual
        const handler = (evt) => {
            try{
                const json = JSON.parse(evt.data);
                onDataRef.current(json);
            }catch (err){
                console.error("Error parsing message:", err);
            }
        };

        // 1. Abrir o reusar la conexion
        connectWS(url);
        // 2. Suscribirse al stream
        suscribeToWS(url, handler);

        // 3. Limpiar al desmontar
        return () => {
            unsubscribeFromWS(url, handler);
            closeWS(url);
        };
    }, [url]); // Solo se vuelve a ejecutar si cambia la url (la clave)
};
