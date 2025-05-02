import { useEffect, useCallback, useRef, use } from "react";
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
    const handelRef = useRef(null);
    const urlRef = useRef(null);


    useEffect(() => {
        // Actualiza la referencia de callback
        onDataRef.current = onData;
    }, [onData]);


    useEffect(() => {
        if (!key) return;

        // Memoriza la url para que cambie solo cuando cambie la clave
        const url = key ? `${import.meta.env.VITE_WS_URL}/candle-stream/${encodeURIComponent(key)}` : null;
        urlRef.current = url;

        // Handler interno que delega en la ref actual
        const handler = (evt) => {
            try{
                const json = JSON.parse(evt.data);
                onDataRef.current(json);
            }catch (err){
                console.error("Error parsing message:", err);
            }
        };
        handelRef.current = handler;

        // Conexión y suscripción
        connectWS(url);
        suscribeToWS(url, handler);

        // 3. Limpiar al desmontar
        return () => {
            if (urlRef.current){
                unsubscribeFromWS(url, handler);
                closeWS(url);
            }
        };
    }, [key]); // Solo se vuelve a ejecutar si cambia la url (la clave)
};
