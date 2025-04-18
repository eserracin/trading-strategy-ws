import React from 'react';
import { useTranslation } from 'react-i18next';

const ActiveSymbolTable = ({ marketData }) => {

    const { t } = useTranslation();
    const symbols = Object.keys(marketData);

    console.log("📝 Active Symbols:", symbols);

    return (
        <div className="overflow-x-auto bg-white shadow-lg rounded-2xl p-6 mt-10 border border-gray-400">

          {/* Encabezado */}
          <div className="flex items-center justify-between border-b border-gray-300 pb-2 mb-4">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">🔍 {t('active_symbols.title')}</h2>
          </div>
          
          {/* Tabla */}
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
                  const data = marketData[symbol];
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
                        <button className="text-blue-600 hover:underline text-xs">Detalles</button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
      </div>    
    );

}

export default ActiveSymbolTable;