import React, { use, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { closeWS } from '../services/ws';
import { stopStrategy } from '../services/api';
import useStrategyStore from '../store/strategyStore';
import ReusableTable from './util/ReusableTable';

const ActiveSymbolTable = ({ marketData }) => {

    const { t } = useTranslation();
    const [symbolsData, setSymbolsData] = useState(marketData);
    const { selectedStrategy } = useStrategyStore();

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
        t('active_symbols.table.price'),
        t('active_symbols.table.change'),
        t('active_symbols.table.high_low'),
        t('active_symbols.table.volume'),
        t('active_symbols.table.actions')
    ];

   const renderRow = (symbol, index) => {
    const data = marketData[symbol];
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
          
          {/* Tabla
          <table className="min-w-full text-sm text-left border-separate border-spacing-y-2">
            <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
              <tr>
                <th className="px-4 py-2 border-r border-gray-200">Name</th>
                <th className="px-4 py-2 border-r border-gray-200">Price</th>
                <th className="px-4 py-2 border-r border-gray-200">24h Change</th>
                <th className="px-4 py-2 border-r border-gray-200">24h High / Low</th>
                <th className="px-4 py-2 border-r border-gray-200">24h Volume</th>
                <th className="px-4 py-2 border-r border-gray-200">Actions</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-200">
              {symbols.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-4 py-4 text-center text-gray-500">
                    {t('active_symbols.no_symbols')}
                  </td>
                </tr>
              ) : (
                symbols.map((symbol) => {
                  const data = symbolsData[symbol];
                  return (
                    <tr key={symbol} className="hover:bg-gray-50 transition duration-150">
                      <td className="px-4 py-2 font-medium">{symbol}</td>
                      <td className="px-4 py-2">{data?.price || '-'}</td>
                      <td className="px-4 py-2">{data?.change24h || '-'}</td>
                      <td className="px-4 py-2">
                        {data?.high24h || '-'} / {data?.low24h || '-'}
                      </td>
                      <td className="px-4 py-2">{data?.volume24h || '-'}</td>
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
                })
              )}
            </tbody>
          </table> */}
      </div>    
    );

}

export default ActiveSymbolTable;