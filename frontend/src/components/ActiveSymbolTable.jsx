
import React, { useState, useEffect, use } from 'react';
import { useTranslation } from 'react-i18next';
import { stopStrategy } from '../services/api';
import useStrategyStore from '../store/strategyStore';
import ReusableTable from './util/ReusableTable';
import { closeWS, connectWS, suscribeToWS, unsubscribeFromWS } from "../services/ws";

const ActiveSymbolTable = ({ marketData }) => {

    const { t } = useTranslation();
    const [symbolsData, setSymbolsData] = useState(marketData || {});

    const activeStrategies = useStrategyStore(state => state.activeStrategies);
    const deactivateStrategy = useStrategyStore(state => state.deactivateStrategy);
    const selectedTimeframe = useStrategyStore(state => state.selectedTimeframe);
    
    const [timeLeft, setTimeLeft] = useState({});
    const [flashSymbols, setFlashSymbols] = useState({});
    const [isLoadingSymbols, setIsLoadingSymbols] = useState({});


    useEffect(() => {
        setSymbolsData(marketData || {});
    }, [marketData]); 

    useEffect(() => {
      const connections = []

      Object.entries(activeStrategies).forEach(([key, config]) => {
        const { symbol, strategyName, socketEnabled } = config;

        console.log(`111 Activando:  estrategia = ${strategyName}, símbolo = ${symbol}, habilitado = ${socketEnabled}`);

        if (!socketEnabled) return;

        const keyLoading = symbol+strategyName;
        const url_ws = import.meta.env.VITE_WS_URL + `/candle-stream/${keyLoading}`;

        connectWS(url_ws);
        setIsLoadingSymbols((prev) => ({ ...prev, [keyLoading]: true }));

        const handleMessage = (data) => {
          if (data.tipo === 'candle') {

            setIsLoadingSymbols((prev) => ({ ...prev, [keyLoading]: false }));

            const symbolStrategyKey = symbol+strategyName;

            setSymbolsData((prevData) => ({
              ...prevData,
              [symbolStrategyKey]: {
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
              [symbolStrategyKey]: Math.max(0, Math.floor((data.close_time - Date.now()) / 1000)),
            }));
          }
        };

        suscribeToWS(url_ws, handleMessage);
        connections.push({ url: url_ws, handler: handleMessage });
      });
        
      return () => {
        connections.forEach(({ url, handler }) => {
          unsubscribeFromWS(url, handler);
          closeWS(url);
        });
      };
    }, [activeStrategies]);

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

    const handleDeactivate = async (symbol, strategyName) => {
      const keyLoading = symbol+strategyName;
      const url_ws = import.meta.env.VITE_WS_URL + `/candle-stream/${keyLoading}`;

      try {
        await stopStrategy(symbol, strategyName);
        unsubscribeFromWS(url_ws);
        closeWS(url_ws);

        deactivateStrategy(symbol, strategyName)

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

   const renderRow = ([symbolStrategyKey, strategyMeta], index) => {
    const data = symbolsData[symbolStrategyKey] || {};
    const isLoadingThisSYmbol = isLoadingSymbols[symbolStrategyKey];
    // const [symbol, strategyName] = symbolStrategyKey.split(/-(?=[^-]+$)/);

    console.log('111 🔄 Renderizando fila:', symbolStrategyKey, strategyMeta, data, isLoadingThisSYmbol);


    if (isLoadingThisSYmbol) {
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
        <td className="px-4 py-2 font-medium">{strategyMeta.symbol}</td>
        <td className="px-4 py-2 font-medium">{strategyMeta.strategyName || '-'}</td>
        <td className="px-4 py-2">{data?.close || '-'}</td>
        <td className="px-4 py-2">{selectedTimeframe || '-'}</td>


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
            onClick={() => handleDeactivate(strategyMeta.symbol, strategyMeta.strategyName)}
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