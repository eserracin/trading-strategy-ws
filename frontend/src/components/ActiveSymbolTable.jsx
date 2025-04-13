import React from 'react';

const ActiveSymbolTable = ({ marketData }) => {

    const symbols = Object.keys(marketData);

    console.log("📝 Active Symbols:", symbols);

    return (
        <div className="overflow-x-auto bg-white shadow-md rounded-xl p-4 mt-10">
        <table className="min-w-full text-sm text-left text-gray-900">
          <thead className="bg-blue-100 text-blue-700 uppercase font-semibold text-xs">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Price</th>
              <th className="px-4 py-3">24h Change</th>
              <th className="px-4 py-3">24h High / Low</th>
              <th className="px-4 py-3">24h Volume</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          {symbols.length === 0 ? (
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td colSpan="6" className="px-4 py-4 text-center text-gray-500">No active symbols</td>
              </tr>
            </tbody>
          ) : (
          <tbody className="divide-y divide-gray-200">
            {symbols.map((sym) => {
              const data = marketData[sym];
              return (
              <tr key={sym}>
                <td className="px-4 py-4 flex items-center gap-2">
                  <img src={data.logoUrl} alt={data.symbol} className="w-5 h-5" />
                  <span className="font-semibold">{data.symbol}</span>
                </td>
                <td className="px-4 py-4 text-gray-600">${data.priceChange}</td>
                <td className="px-4 py-4">
                  <span className={`font-semibold text-xs px-2 py-1 rounded-full ${
                    parseFloat(data.priceChange) >= 0 ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
                  }`}>
                    {data.priceChange}%
                  </span>
                </td>
                <td className="px-4 py-4 text-gray-600">
                  {data.highPrice} / {data.lowPrice}
                </td>
                <td className="px-4 py-4 text-gray-600">{data.volume}</td>
                <td className="px-4 py-4">
                  <a href="#" className="text-blue-500 hover:underline text-xs">Data History</a> ·{' '}
                  <a href="#" className="text-blue-500 hover:underline text-xs">Trade</a>
                </td>
              </tr>
              )
            })}
          </tbody>
          )}
        </table>
      </div>    
    );

}

export default ActiveSymbolTable;