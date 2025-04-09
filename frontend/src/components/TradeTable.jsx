import React, { useEffect, useState } from 'react';
import { connectWS, suscribeToWS, unsubscribeFromWS } from '../services/ws'

const TradeTable = () => {
  const [trades, setTrades] = useState([]);


       useEffect(() => {
        connectWS('ws://localhost:8000/ws/status-stream');

        const handleEvent = (data) => {
          if (data.type === 'nuevo-trade'){
            setTrades((prevEvents) => [...prevEvents.slice(0, 10), data]);
          }
        };

        suscribeToWS(handleEvent);

        return () => {
          unsubscribeFromWS(handleEvent);
        };

      }, []);

  return (
    <div className="mt-10 w-full max-w-4xl bg-white shadow rounded p-4 mx-auto">
      <h2 className="text-xl font-bold mb-4 text-center">📋 Operaciones Activas</h2>
      {trades.length === 0 ? (
        <p className="text-center text-gray-500">Sin operaciones aún</p>
      ) : (

      <table className="w-full text-sm text-left border">
        <thead className="bg-gray-200">
          <tr>
            <th className="p-2">Símbolo</th>
            <th className="p-2">Estrategia</th>
            <th className="p-2">Modo</th>
            <th className="p-2">Entry</th>
            <th className="p-2">SL</th>
            <th className="p-2">TP</th>
            <th className="p-2">Qty</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((t, i) => (
            <tr key={i} className="border-t">
              <td className="p-2">{t.symbol}</td>
              <td className="p-2">{t.strategy}</td>
              <td className="p-2">{t.modo}</td>
              <td className="p-2">{t.entry_price}</td>
              <td className="p-2">{t.sl}</td>
              <td className="p-2">{t.tp}</td>
              <td className="p-2">{t.qty}</td>
            </tr>
          ))}
        </tbody>
      </table>
      )}
    </div>
  );
};

export default TradeTable;
