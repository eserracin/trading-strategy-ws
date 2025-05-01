
import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { stopStrategy } from '../services/api';
import useStrategyStore from '../store/strategyStore';
import ReusableTable from './util/ReusableTable';
import { closeWS, connectWS, suscribeToWS, unsubscribeFromWS } from "../services/ws";

const ActiveSymbolTable = ({ marketData }) => {

    const { t } = useTranslation();
    const [symbolsData, setSymbolsData] = useState(marketData || {});

    const activeStrategies = useStrategyStore(state => state.activeStrategies);
    const deactivateStrategyStore = useStrategyStore(state => state.deactivateStrategy);
    const updateStrategyStatusStore = useStrategyStore(state => state.updateStrategyStatus);
    const connectionRef = useRef(new Map());    
    const [timeLeft, setTimeLeft] = useState({});
    const [flashSymbols, setFlashSymbols] = useState({});


    useEffect(() => {
        setSymbolsData(marketData || {});
    }, [marketData]); 

    useEffect(() => {

      // ---------- Altas ----------------
      Object.entries(activeStrategies).forEach(([key, config]) => {
  
        if (connectionRef.current.has(key)) return;
        const url_ws = `${import.meta.env.VITE_WS_URL}/candle-stream/${key}`;

        const handleMessage = (data) => {
          if (data.tipo === 'candle') {

            setSymbolsData((prevData) => ({
              ...prevData,
              [key]: {
                open: data.open,
                high: data.high,
                Low: data.low,
                close: data.close,
                volume: data.volume,
                interval: data.interval,
                open_time: data.open_time,
                close_time: data.close_time
              }
            }));

            setTimeLeft((prevTimeLeft) => ({
              ...prevTimeLeft,
              [key]: Math.max(0, Math.floor((data.close_time - Date.now()) / 1000)),
            }));

            updateStrategyStatusStore(key, 'loaded');
          }
        };

        connectWS(url_ws);
        suscribeToWS(url_ws, handleMessage);
        connectionRef.current.set(key, { url: url_ws, handler: handleMessage });
      });

      
      // ---------- Bajas ----------------
      connectionRef.current.forEach(({ url, handler }, key) => {
        if (!activeStrategies[key]) {
          unsubscribeFromWS(url, handler);
          closeWS(url);
          connectionRef.current.delete(key);
        }
      });

    }, [activeStrategies]);

    useEffect(() => {
      const interval = setInterval(() => {
        setTimeLeft((prevTimeLeft) => {
          const updatedTimeLeft = {};
          Object.keys(prevTimeLeft).forEach((key) => {
            if (prevTimeLeft[key] > 0) {
              updatedTimeLeft[key] = prevTimeLeft[key] - 1;
            } else {
              // Activamos el parpadeo
              setFlashSymbols((prevFlashSymbols) => ({
                ...prevFlashSymbols,
                [key]: !prevFlashSymbols[key],
              }));

              // Desactivamos el parpadeo después de 3 segundos
              setTimeout(() => {
                setFlashSymbols((prevFlashSymbols) => ({
                  ...prevFlashSymbols,
                  [key]: false,
                }));
              }, 3000);
            }
          });
          return updatedTimeLeft;
        });
      }, 1000);
      return () => clearInterval(interval);
    }, []);

    const handleDeactivate = async (symbol, strategyName, timeframe) => {
      const keyLoading = symbol + strategyName + timeframe;
      const url_ws = import.meta.env.VITE_WS_URL + `/candle-stream/${keyLoading}`;

      try {
        await stopStrategy(symbol, strategyName, timeframe);
        unsubscribeFromWS(url_ws);
        closeWS(url_ws);

        deactivateStrategyStore(symbol, strategyName, timeframe);

        setSymbolsData((prevData) => {
          const updatedData = { ...prevData };
          delete updatedData[keyLoading];
          return updatedData;
        });

        setTimeLeft((prevTimeLeft) => {
          const updatedTimeLeft = { ...prevTimeLeft };
          delete updatedTimeLeft[keyLoading];
          return updatedTimeLeft;
        });

        setFlashSymbols((prevFlashSymbols) => {
          const updatedFlashSymbols = { ...prevFlashSymbols };
          delete updatedFlashSymbols[keyLoading];
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

   const renderRow = ([symbolStrategyKey, strategyMeta], index) => {
    const data = symbolsData[symbolStrategyKey] || {};
    const { symbol, strategyName, timeframe } = strategyMeta;



    if (!symbolsData[symbolStrategyKey]) {
      return (
        <tr key={symbolStrategyKey}>
          <td colSpan={headers.length} className="px-4 py-4 text-center text-blue-600">
            <div className="flex justify-center items-center gap-2">
              <svg className="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              <span>{t('active_symbols.loading')}</span>
            </div>
          </td>
        </tr>
      );
    }

    return (
      <tr key={symbolStrategyKey} className="hover:bg-gray-50 transition duration-150">
        <td className="px-4 py-2 font-medium">{symbol}</td>
        <td className="px-4 py-2 font-medium">{strategyName || '-'}</td>
        <td className="px-4 py-2">{data?.close || '-'}</td>
        <td className="px-4 py-2">{timeframe || '-'}</td>


        <td 
          className={`px-4 py-2 ${flashSymbols[symbolStrategyKey] ? 'animate-pulse bg-yellow-200' : ''}`}
        >{
          timeLeft[symbolStrategyKey] !== undefined 
          ? formatTimeLeft(timeLeft[symbolStrategyKey])
          : '-'}
        </td>


        <td className="px-4 py-2">{data?.volume || '-'}</td>
        <td className="px-4 py-2">
          <button
            onClick={() => handleDeactivate(symbol, strategyName, timeframe)}
            className="text-red-600 hover:underline text-xs"
          >
            {t('active_symbols.deactivate')}
          </button>
        </td>
      </tr>
    );
   };

    const symbolsKey = Object.entries(activeStrategies);

    return (
        <div className="overflow-x-auto bg-white shadow-lg rounded-2xl p-6 mt-10 border border-gray-400">

          {/* Encabezado */}
          <div className="flex items-center justify-between border-b border-gray-300 pb-2 mb-4">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">🔍 {t('active_symbols.title')}</h2>
          </div>

          <ReusableTable
            headers={headers}
            data={symbolsKey}
            renderRow={renderRow}
            noDataMessage={t('active_symbols.no_symbols')}
            className="min-w-full text-sm text-left border-separate border-spacing-y-2"
          />  
      </div>    
    );

}

export default ActiveSymbolTable;