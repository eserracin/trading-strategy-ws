import React, { useState, useEffect } from 'react';
// import axios from 'axios';
import ActiveSymbolTable from './ActiveSymbolTable/ActiveSymbolTable';
import StrategyButton from './StrategyButton';
import EntrySignalTable from './EntrySignalTable';
import SideBar from './ui/SideBar';
import { useTranslation } from 'react-i18next';

const TradingStrategyDashboard = () => {

    const { t } = useTranslation();

    // 🔹 Simulamos datos de usuario con avatar:
    const user = {
        avatarUrl: '/default-avatar.png', // o trae este valor desde tu backend
        name: 'John Doe'
    };

    return(
        <div className="flex h-screen w-full">

            {/* 🔹 Sidebar */}
            <SideBar user={user}/>

            {/* 🔹 Contenido principal */}
            <main className="flex-1 bg-gray-50 overflow-y-auto">
                <div className="px-6 py-6 space-y-6">
                    <h1 className="text-3xl font-bold text-center text-blue-700">📊 {t('dashboard.title')}</h1>
                    <StrategyButton/>
                    <ActiveSymbolTable/>

                    <div className="my-4">
                        <EntrySignalTable />
                    </div>
                </div>
            </main>
        </div>
    )
}

export default TradingStrategyDashboard;