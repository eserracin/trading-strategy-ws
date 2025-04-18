import { useEffect, useState } from "react";
import { connectWS, suscribeToWS, unsubscribeFromWS } from "../services/ws";
import useStrategyStore from "../store/strategyStore";

const EntrySignalTable = (enableSocket) => {
  const [entries, setEntries] = useState([]);
  const socketEnabled = useStrategyStore((state) => state.socketEnabled);

  useEffect(() => {
    if (!socketEnabled) {
      return;
    }

    // Establish WebSocket connection
    // and subscribe to the status stream
    connectWS("ws://localhost:8000/ws/status-stream");

    const handleMessage = (data) => {
      if (data.type === "nuevo-trade") {

        const newEntry = {
          date: new Date().toLocaleString("en-GB"),
          pair: data.symbol,
          type: data.type,
          side: data.side,
          price: data.price,
          amount: data.executedQty
        };

        setEntries((prevEntries) => [newEntry, ...prevEntries.slice(0, 49)]); // Limit to 5 entries
      }
    } 

    suscribeToWS(handleMessage);

    return () => {
      unsubscribeFromWS(handleMessage);
    };
  }, [socketEnabled]);

  return (

    <div className="max-w-6xl mx-auto bg-white rounded-lg shadow-md border border-gray-400 p-6">

      {/* Encabezado */}
      <div className="flex items-center justify-between border-b border-gray-300 pb-2 mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Future Status</h2>
        <div className="flex space-x-16 mt-3 ">
          <button className="text-yellow-500 font-medium border-b-2  pb-2">Open-Order</button>
          <button className="text-gray-400">Order-History</button>
          <button className="text-gray-400">Trade-History</button>
        </div>
      </div>


      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm border-separate border-spacing-y-2">
          <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-2 border-r border-gray-200">Date</th>
              <th className="px-4 py-2 border-r border-gray-200">Pair</th>
              <th className="px-4 py-2 border-r border-gray-200">Type</th>
              <th className="px-4 py-2 border-r border-gray-200">Side</th>
              <th className="px-4 py-2 border-r border-gray-200">Price</th>
              <th className="px-4 py-2 border-r border-gray-200">Amount</th>
              <th className="px-4 py-2 border-r border-gray-200">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {entries.map((entry, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-4 py-2 border-r border-gray-100">{entry.date}</td>
                <td className="px-4 py-2 border-r border-gray-100">{entry.pair}</td>
                <td className="px-4 py-2 border-r border-gray-100">{entry.type}</td>
                <td className="px-4 py-2 border-r border-gray-100 text-green-600">{entry.side}</td>
                <td className="px-4 py-2 border-r border-gray-100">{entry.price}</td>
                <td className="px-4 py-2 border-r border-gray-100">{entry.amount}</td>
                <td className="px-4 py-2 flex space-x-2">
                  <button className="text-blue-500 hover:text-blue-700">Edit</button>
                  <button className="text-red-500 hover:text-red-700">Delete</button>
                </td>
              </tr> 
            ))}

            {/* <tr className="hover:bg-gray-50">
              <td className="px-4 py-2 border-r border-gray-100">09-18 17:32:15</td>
              <td className="px-4 py-2 border-r border-gray-100">ETH/USDT</td>
              <td className="px-4 py-2 border-r border-gray-100">Limit</td>
              <td className="px-4 py-2 border-r border-gray-100 text-green-600">Buy</td>
              <td className="px-4 py-2 border-r border-gray-100">2774.00</td>
              <td className="px-4 py-2 border-r border-gray-100">0.000378</td>
              <td className="px-4 py-2 flex space-x-2">
              </td>
            </tr> */}
          </tbody>
        </table>
      </div>
      
    </div>
  );
};

export default EntrySignalTable;
