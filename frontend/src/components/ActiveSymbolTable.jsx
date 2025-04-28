import React, { use, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { closeWS } from '../services/ws';
import { stopStrategy } from '../services/api';
import useStrategyStore from '../store/strategyStore';
import ReusableTable from './util/ReusableTable';
import { connectWS, suscribeToWS, unsubscribeFromWS } from "../services/ws";

const ActiveSymbolTable = ({ marketData }) => {

    const { t } = useTranslation();
    const [symbolsData, setSymbolsData] = useState(marketData);
    const { selectedStrategy } = useStrategyStore();
    const socketEnabled = useStrategyStore((state) => state.socketEnabled);

    const handleDeactivate = async (symbol) => {
      try {
        await stopStrategy(symbol, selectedStrategy);
        closeWS();
        const updatedSymbols = { ...symbolsData };
        delete updatedSymbols[symbol];
        setSymbolsData(updatedSymbols);
        window.location.reload();
      } catch (error) {
        console.error('Error sending unsubscribe message:', error);
      }

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
    // const data = marketData[symbol];

    useEffect(() => {
      if (!socketEnabled) {
        return;
      }

      const url_ws = import.meta.env.VITE_WS_URL + '/candle-stream';

      connectWS(url_ws);

      const handleMessage = (data) => {
        if (data.tipo === 'candle') {
          setSymbolsData((prevData) => ({
            ...prevData,
            [data.symbol]: data
          }));
        }
      };

      suscribeToWS(url, handleMessage);

      return () => {
        unsubscribeFromWS(url, handleMessage);
      };
    }, [socketEnabled]);


    return (
      <tr key={symbol} className="hover:bg-gray-50 transition duration-150">
        <td className="px-4 py-2 font-medium">{symbol}</td>
        <td className="px-4 py-2">{data?.lastPrice || '-'}</td>
        <td className="px-4 py-2">{data?.priceChange || '-'}</td>
        <td className="px-4 py-2">{data?.highPrice || '-'} / {data?.lowPrice || '-'}</td>
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


    const symbols = Object.keys(marketData);

    console.log("📝 Active Symbols:", symbols);

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