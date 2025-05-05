// src/components/ActiveSymbolTable/ActiveSymbolTable.jsx
import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { stopStrategy } from '../../services/api';
import useStrategyStore from '../../store/strategyStore';
import ReusableTable from '../ui/ReusableTable';
import ActiveSymbolRow from './ActiveSymbolRow';

const ActiveSymbolTable = () => {
  const { t } = useTranslation();
  const [symbolsData, setSymbolsData] = useState({});
  const [timeLeft, setTimeLeft] = useState({});
  const [flashSymbols, setFlashSymbols] = useState({});

  const activeStrategies = useStrategyStore(state => state.activeStrategies);
  const deactivateStrategyStore = useStrategyStore(state => state.deactivateStrategy);
  const updateStrategyStatusStore = useStrategyStore(state => state.updateStrategyStatus);

  // Cronómetro visual
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeLeft(prev => {
        const updated = {};
        Object.keys(prev).forEach(key => {
          if (prev[key] > 0) {
            updated[key] = prev[key] - 1;
          } else {
            setFlashSymbols(f => ({ ...f, [key]: !f[key] }));
            setTimeout(() => setFlashSymbols(f => ({ ...f, [key]: false })), 3000);
          }
        });
        return updated;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);


  const handleDeactivate = async (symbol, strategyName, timeframe) => {
    const key = symbol + strategyName + timeframe;
    try {
      await stopStrategy(symbol, strategyName, timeframe);
      deactivateStrategyStore(symbol, strategyName, timeframe);
      setSymbolsData(d => {
        const updated = { ...d };
        delete updated[key];
        return updated;
      });
      setTimeLeft(t => {
        const updated = { ...t };
        delete updated[key];
        return updated;
      });
      setFlashSymbols(f => {
        const updated = { ...f };
        delete updated[key];
        return updated;
      });
    } catch (err) {
      console.error('Error al desactivar estrategia:', err);
    }
  };

  const formatTimeLeft = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const headers = [
    t('active_symbols.table.name'),
    t('active_symbols.table.strategy'),
    t('active_symbols.table.price'),
    t('active_symbols.table.interval'),
    t('active_symbols.table.close_time'),
    t('active_symbols.table.volume'),
    t('active_symbols.table.actions')
  ];

  
  const renderRow = ([key, { symbol, strategyName, timeframe }]) => {
        
    const onCandle = (data) => {
      // console.log("🏷️ [ActiveSymbolRow] onCandle data:", data);
      
      if (data.tipo !== 'candle') return;
  
      setSymbolsData(prev => ({
        ...prev,
        [key]: {
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
          volume: data.volume,
          interval: data.interval,
          open_time: data.open_time,
          close_time: data.close_time
        }
      }));
  
      setTimeLeft(prev => ({
        ...prev,
        [key]: Math.max(0, Math.floor((data.close_time - Date.now()) / 1000))
      }));
  
      updateStrategyStatusStore(key, 'loaded');
    };
  
    const data = symbolsData[key];
  
    return (
      <ActiveSymbolRow key={key} keyId={key} onCandle={onCandle}>
        {!data ? (
          <tr>
            <td colSpan={headers.length} className="px-4 py-4 text-center text-blue-600">
              <div className="flex justify-center items-center gap-2">
                <svg className="animate-spin h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                <span>{t('active_symbols.loading')}</span>
              </div>
            </td>
          </tr>
        ) : (
          <tr className="hover:bg-gray-50">
            <td className="px-4 py-2 font-medium">{symbol}</td>
            <td className="px-4 py-2 font-medium">{strategyName || '-'}</td>
            <td className="px-4 py-2">{data?.close || '-'}</td>
            <td className="px-4 py-2">{timeframe || '-'}</td>
            <td className={`px-4 py-2 ${flashSymbols[key] ? 'animate-pulse bg-yellow-200' : ''}`}>
              {timeLeft[key] !== undefined ? formatTimeLeft(timeLeft[key]) : '-'}
            </td>
            <td className="px-4 py-2">{data?.volume || '-'}</td>
            <td className="px-4 py-2">
              <button onClick={() => handleDeactivate(symbol, strategyName, timeframe)} className="text-red-600 hover:underline text-xs">
                {t('active_symbols.deactivate')}
              </button>
            </td>
          </tr>
        )}
      </ActiveSymbolRow>
    );
  };
  

  return (
    <div className="overflow-x-auto bg-white shadow-lg rounded-2xl p-6 mt-10 border border-gray-400">
      <div className="flex items-center justify-between border-b border-gray-300 pb-2 mb-4">
        <h2 className="text-lg font-semibold mb-4 text-gray-800">🔍 {t('active_symbols.title')}</h2>
      </div>
      <ReusableTable
        headers={headers}
        data={Object.entries(activeStrategies)}
        renderRow={renderRow}
        noDataMessage={t('active_symbols.no_symbols')}
        className="min-w-full text-sm text-left border-separate border-spacing-y-2"
      />
    </div>
  );
};

export default ActiveSymbolTable;
