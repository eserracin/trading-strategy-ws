import React, { useState, useEffect } from 'react';
// import axios from 'axios';
import ActiveSymbolTable from './ActiveSymbolTable';
import StrategyButton from './StrategyButton';
import { getMarketData } from '../services/api';

const TradingStrategyDashboard = () => {
    const [ marketData, setMarketData ] = useState({});

    const fetchMarketData = async (symbol) => {
        try {
            const response = await getMarketData(symbol);
            setMarketData((prevData) => ({
                ...prevData,
                [symbol]: response
            }));
            console.log("📝 Market Data:", marketData);
        } catch (error) {
            console.error('Error fetching market data:', error);
        }
    };

    return(
        <div>
            <h1 className="text-3xl font-bold text-center text-blue-700">📊 Trading Dashboard</h1>  
            <StrategyButton onExecuteStrategy={fetchMarketData} />
            <ActiveSymbolTable marketData={marketData} />
        </div>
    )
}

export default TradingStrategyDashboard;