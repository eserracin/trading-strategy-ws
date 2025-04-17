import { useEffect, useState } from "react";
import { connectWS, suscribeToWS, unsubscribeFromWS } from "../services/ws";

const EntrySignalTable = (enableSocket) => {
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    const ws = connectWS("ws://localhost:8000/ws/status-stream");

    const handleMessage = (data) => {
      if (data.type === "nuevo-trade") {
        setEntries((prevEntries) => [...prevEntries, data]);
      }
    } 

    suscribeToWS(handleMessage);

    return () => {
      unsubscribeFromWS(handleMessage);
      ws.close();
    };
  }, []);

  return (
    <div className="overflow-x-auto shadow-md rounded-xl p-4 bg-white">
      <h2 className="text-xl font-semibold mb-4">Future Status</h2>
      <div className="tabs mb-2">
        <a className="tab tab-bordered tab-active">Open-Order</a>
        <a className="tab tab-bordered">Order-History</a>
        <a className="tab tab-bordered">Trade-History</a>
      </div>
    </div>
  );
};

export default EntrySignalTable;
