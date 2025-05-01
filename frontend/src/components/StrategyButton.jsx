import React, { useState, useEffect, useRef } from 'react';
import { fetchStrategies, startStrategy, searchSymbols, createActiveSymbol } from '../services/api';
import useStrategyStore from '../store/strategyStore';
import timeframes from '../assets/config/timeframes.json';

const StrategyButton = ({ onExecuteStrategy }) => {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [selectedTimeframe, setSelectedTimeframe] = useState('');
  const [symbolQuery, setSymbolQuery] = useState('');
  const [symbolSuggestions, setSymbolSuggestions] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const inputRef = useRef(null);
  const symbolCache = useRef(new Map());

  const activateStrategyStore = useStrategyStore((state) => state.activateStrategy);
  const setSelectedStrategyStore = useStrategyStore((state) => state.setSelectedStrategy);
  const activeStrategies = useStrategyStore((state) => state.activeStrategies);

  const [isActivatable, setIsActivatable] = useState(false);

  useEffect(() => {
    const strategy = strategies.find((s) => s.name === selectedStrategy);
    setSelectedTimeframe(strategy?.timeframe || '');
  }, [selectedStrategy, strategies]);

  // Carga inicial de estrategias
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        const data = await fetchStrategies();
        setStrategies(data);
      } catch (error) {
        console.error('❌ Error fetching strategies:', error);
      }
    };

    loadStrategies();
  }, []);

  // Activar el boton de activar estrategia si hay un símbolo y una estrategia seleccionados
  useEffect(() => {
    const key = selectedSymbol + selectedStrategy + selectedTimeframe;
    const alreadyExists = !!activeStrategies[key];
    setIsActivatable(
      selectedSymbol && selectedStrategy && selectedTimeframe && !alreadyExists
    );
  }, [selectedSymbol, selectedStrategy, selectedTimeframe, activeStrategies]);

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      if (symbolQuery.length < 2) {
        setSymbolSuggestions([]);
        return;
      }

      const fetchSuggestions = async () => {
        const query = symbolQuery.toUpperCase();
        const cached = symbolCache.current.get(query);
        if (cached) {
          console.log('📦 Usando caché:', query);
          setSymbolSuggestions(cached);
          return;
        }

        console.log('🔍 Buscando en API:', query);
        const results = await searchSymbols(query);
        console.log('📥 Resultados:', results);
        symbolCache.current.set(query, results);
        setSymbolSuggestions(results);
      };

      fetchSuggestions();
    }, 300);

    return () => clearTimeout(delayDebounce);
  }, [symbolQuery]);


  // Evento Click => Boton de activar estrategia
  const handleClick = async () => {
      if (!selectedStrategy || !selectedSymbol || !selectedTimeframe) {
        alert('Debes seleccionar símbolo, estrategia y temporalidad.');
        return;
      }

    try {
      await startStrategy(selectedSymbol, selectedStrategy, selectedTimeframe);
      // await createActiveSymbol(selectedSymbol, selectedStrategy);
      onExecuteStrategy(selectedSymbol);
      activateStrategyStore(selectedSymbol, selectedStrategy, selectedTimeframe);
      setSelectedStrategyStore(selectedSymbol, selectedStrategy, selectedTimeframe);
    } catch (error) {
      console.error('❌ Error ejecutando estrategia:', error);
    }
  };

  const handleReset = () => {
    setSymbolQuery('');
    setSelectedSymbol('');
    setSelectedStrategy('');
    setSelectedTimeframe('');
    setIsActivatable(false);
  };

  return (
    <div className="bg-blue-50 border border-blue-400 rounded-lg shadow p-4 w-full max-w-5xl mx-auto">

      {/* Encabezado */}
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-primary font-semibold text-base flex items-center gap-2">
          <svg className="w-5 h-5 fill-blue-600" viewBox="0 0 24 24">
            <path d="M3 4a1 1 0 0 1 1-1h16a1 1 0 0 1 .8 1.6L15 13.2V19a1 1 0 0 1-1.45.9l-4-2A1 1 0 0 1 9 17v-3.8L3.2 4.6A1 1 0 0 1 3 4z"/>
          </svg>
          Filtro
        </h3>
      </div>

      {/* Contenido */}
      <div className="grid grid-cols-4 gap-4 items-start">

        {/* Símbolo */}
        <div className="relative">
          <label className="block text-sm font-medium text-muted mb-1">Símbolo</label>
          <input
            ref={inputRef}
            type="text"
            placeholder="BTCUSDT"
            className="w-full p-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={symbolQuery}
            onChange={(e) => {
              setSymbolQuery(e.target.value.toUpperCase());
              setSelectedSymbol('');
              setHighlightedIndex(-1);
            }}
            onKeyDown={(e) => {
              if (symbolSuggestions.length === 0) return;

              if (e.key === 'ArrowDown') {
                e.preventDefault();
                setHighlightedIndex((prev) => Math.min(prev + 1, symbolSuggestions.length - 1));
              } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setHighlightedIndex((prev) => Math.max(prev - 1, -1));
              } else if (e.key === 'Enter' && highlightedIndex !== -1) {
                  const selected = symbolSuggestions[highlightedIndex];
                  setSelectedSymbol(selected);
                  setSymbolQuery(selected);
                  setSymbolSuggestions([]);
                  setHighlightedIndex(-1);
                }
            }}
          />
          {symbolSuggestions.length > 0 && (
            <ul className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow max-h-48 overflow-y-auto">
              {symbolSuggestions.map(sym => (
                <li
                  key={sym}
                  onClick={() => {
                    setSelectedSymbol(sym);
                    setSymbolQuery(sym);
                    setSymbolSuggestions([]);
                  }}
                  className="px-3 py-2 hover:bg-blue-100 cursor-pointer text-sm"
                >
                  {sym}
                </li>
              ))}
            </ul>
          )}
        </div>


        {/* Estrategia */}
        <div>
          <label className="block text-sm font-medium text-muted mb-1">Estrategia</label>
          <select
            className="w-full p-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
          >
            <option value="">Selecciona estrategia</option>
            {strategies.map((strat) => (
              <option key={strat} value={strat}>{strat}</option>
            ))}
          </select>
        </div>


        {/* Temporalidad */}
        <div>
          <label className="block text-sm font-medium text-muted mb-1">Temporalidad</label>
          <select
            className="w-full p-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            disabled={!selectedStrategy}
          >
            <option value="">Selecciona temporalidad</option>
            {timeframes.map((tf) => (
              <option key={tf.value} value={tf.value}>{tf.label}</option>
            ))}
          </select>
        </div>


        { /* Botones Activar y Limpiar */}
        <div className="flex gap-2 pt-7">
          <button
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-md transition disabled:opacity-50"
            onClick={handleClick}
            disabled={!isActivatable}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="white">
              <path d="M3 4a1 1 0 0 1 1-1h16a1 1 0 0 1 .8 1.6L15 13.2V19a1 1 0 0 1-1.45.9l-4-2A1 1 0 0 1 9 17v-3.8L3.2 4.6A1 1 0 0 1 3 4z"/>
            </svg>
            Activar
          </button>
          <button
            className="bg-red-100 text-red-600 hover:bg-red-200 text-sm font-medium px-4 py-2 rounded-md"
            onClick={handleReset}
          >
            Limpiar
          </button>
        </div>
      </div>
    </div>
  );
};

export default StrategyButton;
