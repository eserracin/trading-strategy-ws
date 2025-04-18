import React, { useState, useEffect } from 'react';
// import axios from 'axios';
import ActiveSymbolTable from './ActiveSymbolTable';
import StrategyButton from './StrategyButton';
import EntrySignalTable from './EntrySignalTable';
import { getMarketData } from '../services/api';
import { useTranslation } from 'react-i18next';

const TradingStrategyDashboard = () => {
    const [ marketData, setMarketData ] = useState({});
    const { t } = useTranslation();

    const fetchMarketData = async (symbol) => {
        try {
            const response = await getMarketData(symbol);
            setMarketData((prevData) => ({
                ...prevData,
                [symbol]: response
            }));
        } catch (error) {
            console.error('Error fetching market data:', error);
        }
    };

    return(
        <div className="flex flex-col gap-6">
            <h1 className="text-3xl font-bold text-center text-blue-700">📊 {t('dashboard.title')}</h1>  
            <StrategyButton onExecuteStrategy={fetchMarketData} />
            <ActiveSymbolTable marketData={marketData} />

            <div className="my-4">
                <EntrySignalTable />
            </div>
        </div>
    )
}

export default TradingStrategyDashboard;