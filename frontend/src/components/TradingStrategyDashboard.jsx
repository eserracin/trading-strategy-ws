import React, { useState, useEffect } from 'react';
// import axios from 'axios';
import ActiveSymbolTable from './ActiveSymbolTable/ActiveSymbolTable';
import StrategyButton from './StrategyButton';
import EntrySignalTable from './EntrySignalTable';
import { useTranslation } from 'react-i18next';

const TradingStrategyDashboard = () => {

    const { t } = useTranslation();

    return(
        <div className="flex flex-col gap-6">
            <h1 className="text-3xl font-bold text-center text-blue-700">📊 {t('dashboard.title')}</h1>  
            <StrategyButton/>
            <ActiveSymbolTable/>

            <div className="my-4">
                <EntrySignalTable />
            </div>
        </div>
    )
}

export default TradingStrategyDashboard;