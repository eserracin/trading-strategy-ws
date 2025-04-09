import React from 'react';

const ActiveSymbolTable = ({ activeSymbols }) => {
    // if (activeSymbols.length === 0) {
    //     // return <div>No active symbols</div>;
    //     let noActiveSymbolsMessage = "No active symbols";
    //     let noActiveSymbol = true
    // }

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
          {activeSymbols.length === 0 ? (
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td colSpan="6" className="px-4 py-4 text-center text-gray-500">No active symbols</td>
              </tr>
            </tbody>
          ) : (
          <tbody className="divide-y divide-gray-200">
            {activeSymbols.map((sym) => (
              <tr key={sym.symbol}>
                <td className="px-4 py-4 flex items-center gap-2">
                  <img src={sym.logoUrl} alt={sym.symbol} className="w-5 h-5" />
                  <span className="font-semibold">{sym.symbol}</span>
                </td>
                <td className="px-4 py-4 text-gray-600">${sym.price}</td>
                <td className="px-4 py-4">
                  <span className={`font-semibold text-xs px-2 py-1 rounded-full ${
                    parseFloat(sym.change24h) >= 0 ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
                  }`}>
                    {sym.change24h}%
                  </span>
                </td>
                <td className="px-4 py-4 text-gray-600">
                  {sym.high24h} / {sym.low24h}
                </td>
                <td className="px-4 py-4 text-gray-600">{sym.volume24h}</td>
                <td className="px-4 py-4">
                  <a href="#" className="text-blue-500 hover:underline text-xs">Data History</a> ·{' '}
                  <a href="#" className="text-blue-500 hover:underline text-xs">Trade</a>
                </td>
              </tr>
            ))}
          </tbody>
          )}
        </table>
      </div>    
    );

}

export default ActiveSymbolTable;