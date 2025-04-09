import React, { useEffect, useState} from 'react';
import { connectWS, suscribeToWS, unsubscribeFromWS } from '../services/ws'

const LiveEvents = () => {
    const [events, setEvents] = useState([]);

       useEffect(() => {
        connectWS('ws://localhost:8000/ws/status-stream');

        const handleEvent = (data) => {
          if (data.type === 'nuevo-trade'){
            setEvents((prevEvents) => [...prevEvents.slice(0, 10), data]);
          }
        };

        suscribeToWS(handleEvent);

        return () => {
          unsubscribeFromWS(handleEvent);
        };

      }, []);


    return (
        <div className="max-w-4xl mx-auto mt-8 p-4 bg-white shadow rounded">
          <h2 className="text-xl font-semibold mb-4 text-center">⚡ Eventos en Tiempo Real</h2>
          {events.length === 0 ? (
            <p className="text-center text-gray-500">Sin señales aún</p>
          ) : (
            <ul className="space-y-2">
              {events.map((ev, i) => (
                <li key={i} className="bg-gray-100 p-2 rounded text-sm">
                  <strong>{ev.symbol}</strong> - <span className="text-blue-700">{ev.modo}</span> @ {ev.entry} (SL: {ev.sl}, TP: {ev.tp}, QTY: {ev.qty})
                </li>
              ))}
            </ul>
          )}
        </div>
      );
}

export default LiveEvents;