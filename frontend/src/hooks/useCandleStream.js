// src/hooks/useCandleStream.js
import { useEffect, useRef } from "react";
import { connectWS, suscribeToWS, unsubscribeFromWS, closeWS } from "../services/ws";

/**
 * Suscribe a un stream de velas ("candles") para la clave dada y
 * ejecuta onData cada vez que llega un mensaje.
 *
 * @param {string} key        - Formato "SYMBOL::STRATEGY::TF"
 * @param {(data: any) => void} onData
 */
export const useCandleStream = (key, onData) => {
  const onDataRef = useRef(onData);
  onDataRef.current = onData;

  const url = key ? `${import.meta.env.VITE_WS_URL}/candle-stream/${encodeURIComponent(key)}` : null;
  
  const handlerRef = useRef(null);
  const urlRef = useRef(null);
  const connectedRef = useRef(false);

  useEffect(() => {
    if (!url) return;

    urlRef.current = url;
    connectedRef.current = true;

    const handler = (data) => {
      try {
        onDataRef.current(data);
      } catch (err) {
        console.error("🔴 Error parsing message in useCandleStream:", err);
      }
    };

    connectWS(url);
    suscribeToWS(url, handler);
    handlerRef.current = handler;

    return () => {
      // Previene cierres múltiples innecesarios si ya se limpió por un render anterior
      if (connectedRef.current) return;
      connectedRef.current = false;

      if (urlRef.current) {
        unsubscribeFromWS(urlRef.current, handlerRef.current);
        closeWS(urlRef.current);
      }
    };
  }, [url]); // Solo depende de la URL real (codificada)
};
