import React, { useState, useEffect, use } from 'react';
import { useTranslation } from 'react-i18next';
import { stopStrategy } from '../services/api';
import useStrategyStore from '../store/strategyStore';
import ReusableTable from './util/ReusableTable';
import { closeWS, connectWS, suscribeToWS, unsubscribeFromWS } from "../services/ws";

const ActiveSymbolTable = ({ marketData }) => {

    const { t } = useTranslation();
    const [symbolsData, setSymbolsData] = useState(marketData || {});
    const { selectedStrategy } = useStrategyStore();
    const socketEnabled = useStrategyStore((state) => state.socketEnabled);
    const [timeLeft, setTimeLeft] = useState({});
    const [flashSymbols, setFlashSymbols] = useState({});

    const url_ws = import.meta.env.VITE_WS_URL + '/candle-stream';


    useEffect(() => {
        setSymbolsData(marketData || {});
    }, [marketData]); 

    useEffect(() => {
      if (!socketEnabled) return;

      connectWS(url_ws);

      const handleMessage = (data) => {
        if (data.tipo === 'candle') {

          setSymbolsData((prevData) => ({
            ...prevData,
            [data.symbol]: {
              open: data.open,
              high: data.high,
              Low: data.low,
              close: data.close,
              volume: data.volume,
              open_time: data.open_time,
              close_time: data.close_time,
            }
          }));

          setTimeLeft((prevTimeLeft) => ({
            ...prevTimeLeft,
            [data.symbol]: Math.max(0, Math.floor((data.close_time - Date.now()) / 1000)),
          }));
        }
      };

      suscribeToWS(url_ws, handleMessage);

      return () => {
        unsubscribeFromWS(url_ws, handleMessage);
      };
    }, [socketEnabled]);

    useEffect(() => {
      const interval = setInterval(() => {
        setTimeLeft((prevTimeLeft) => {
          const updatedTimeLeft = {};
          Object.keys(prevTimeLeft).forEach((symbol) => {
            if (prevTimeLeft[symbol] > 0) {
              updatedTimeLeft[symbol] = prevTimeLeft[symbol] - 1;
            } else {
              // Activamos el parpadeo
              setFlashSymbols((prevFlashSymbols) => ({
                ...prevFlashSymbols,
                [symbol]: !prevFlashSymbols[symbol],
              }));

              // Desactivamos el parpadeo después de 3 segundos
              setTimeout(() => {
                setFlashSymbols((prevFlashSymbols) => ({
                  ...prevFlashSymbols,
                  [symbol]: false,
                }));
              }, 3000);
            }
          });
          return updatedTimeLeft;
        });
      }, 1000);
      return () => clearInterval(interval);
    }, []);

    const handleDeactivate = async (symbol) => {
      try {
        await stopStrategy(symbol, selectedStrategy);
        closeWS(url_ws);

        setSymbolsData((prevData) => {
          const updatedData = { ...prevData };
          delete updatedData[symbol];
          return updatedData;
        });

        setTimeLeft((prevTimeLeft) => {
          const updatedTimeLeft = { ...prevTimeLeft };
          delete updatedTimeLeft[symbol];
          return updatedTimeLeft;
        });

        setFlashSymbols((prevFlashSymbols) => {
          const updatedFlashSymbols = { ...prevFlashSymbols };
          delete updatedFlashSymbols[symbol];
          return updatedFlashSymbols;
        });

      } catch (error) {
        console.error('Error sending unsubscribe message:', error);
      }

   };

    const formatTimeLeft = (seconds) => {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainingSeconds = seconds % 60;

      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    const headers = [
        t('active_symbols.table.name'),
        t('active_symbols.table.strategy'),
        t('active_symbols.table.price'),
        t('active_symbols.table.interval'),
        t('active_symbols.table.close_time'),
        t('active_symbols.table.volume'),
        t('active_symbols.table.actions')
    ];

   const renderRow = (symbol, index) => {
    const data = symbolsData[symbol] || {};

    return (
      <tr key={symbol} className="hover:bg-gray-50 transition duration-150">
        <td className="px-4 py-2 font-medium">{symbol}</td>
        <td className="px-4 py-2 font-medium">{selectedStrategy || '-'}</td>
        <td className="px-4 py-2">{data?.close || '-'}</td>
        <td className="px-4 py-2">{data?.interval || '-'}</td>


        <td 
          className={`px-4 py-2 ${flashSymbols[symbol] ? 'animate-pulse bg-yellow-200' : ''}`}
        >{
          timeLeft[symbol] !== undefined 
          ? formatTimeLeft(timeLeft[symbol])
          : '-'}
        </td>


        <td className="px-4 py-2">{data?.volume || '-'}</td>
        <td className="px-4 py-2">
          <button
            onClick={() => handleDeactivate(symbol)}
            className="text-red-600 hover:underline text-xs"
          >
            {t('active_symbols.deactivate')}
          </button>
        </td>
      </tr>
    );
  };


    const symbols = Object.keys(symbolsData);

    // console.log("📝 Active Symbols:", symbols);

    return (
        <div className="overflow-x-auto bg-white shadow-lg rounded-2xl p-6 mt-10 border border-gray-400">

          {/* Encabezado */}
          <div className="flex items-center justify-between border-b border-gray-300 pb-2 mb-4">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">🔍 {t('active_symbols.title')}</h2>
          </div>

          <ReusableTable
            headers={headers}
            data={symbols}
            renderRow={renderRow}
            noDataMessage={t('active_symbols.no_symbols')}
            className="min-w-full text-sm text-left border-separate border-spacing-y-2"
          />  
      </div>    
    );

}

export default ActiveSymbolTable;