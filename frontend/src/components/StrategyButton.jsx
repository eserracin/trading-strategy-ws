import React, { useState, useEffect, useRef } from 'react';
import { fetchStrategies, executeStrategy, searchSymbols } from '../services/api';

const StrategyButton = ({ onExecuteStrategy }) => {
    const [strategies, setStrategies] = useState([]);
    const [selectedStrategy, setSelectedStrategy] = useState('');

    const [symbolQuery, setSymbolQuery] = useState(''); // Default symbol
    const [symbolSuggestions, setSymbolSuggestions] = useState([]);
    const [selectedSymbol, setSelectedSymbol] = useState('');
    const symbolCache = useRef(new Map());

    const [highlightedIndex, setHighlightedIndex] = useState(-1);
    const inputRef = useRef(null);

    /** Cargar las Estrategias cuando el componente se monta, se ejecuta una sola vez */
    useEffect(() => {
        const loadStrategies = async () => {
            try {
                const data = await fetchStrategies();
                setStrategies(data.disponibles);
            } catch (error) {
                console.error('Error fetching strategies:', error);
            }
        };

        loadStrategies();
    }, []);

    // Funcion para buscar symbols , usando debounce y cache con useEffect
    useEffect(() => {
      const delayDebounce = setTimeout(() => {

        console.log('🔁 symbolQuery cambió a:', symbolQuery);

        if (symbolQuery.length < 2) {
          console.log('⚠️ Menos de 2 letras, no se busca nada.');
          setSymbolSuggestions([]);
          return;
        }
    
        const fetchSuggestions = async () => {
          const query = symbolQuery.toUpperCase();
          const cached = symbolCache.current.get(symbolQuery.toUpperCase());
          if (cached) {
            console.log('📦 Usando caché para:', query);
            setSymbolSuggestions(cached);
            return;
          }
          
          console.log('🔍 Buscando en API para:', query);
          const results = await searchSymbols(symbolQuery);
          console.log('📥 Resultados de API:', results);
          const symbols = results.symbols;
          symbolCache.current.set(symbolQuery.toUpperCase(), symbols);
          setSymbolSuggestions(symbols);
        };
    
        fetchSuggestions();
      }, 300); // 300ms debounce
    
      return () => {
        console.log('⏱ Cancelando debounce anterior para:', symbolQuery);
        clearTimeout(delayDebounce)
      };
    }, [symbolQuery]);


    

    const handleClick = async () => {
        try {
            if (!selectedStrategy) {
                return alert('Please select a strategy to execute.');
            }
            await executeStrategy(selectedSymbol, selectedStrategy);
            onExecuteStrategy(selectedSymbol);
        } catch (error) {
            console.error('Error executing strategy:', error);
        }
    };

    const handleReset = () => {
      setSymbolQuery('');
      setSelectedSymbol('');
      setSelectedStrategy('');
      // setSelectedDate('');
    };

    return (
        <div className="bg-blue-50 border border-blue-400 rounded-lg shadow p-4 w-full max-w-5xl mx-auto">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-primary font-semibold text-base flex items-center gap-2">
              <svg className="w-5 h-5 fill-blue-600" viewBox="0 0 24 24"><path d="M3 4a1 1 0 0 1 1-1h16a1 1 0 0 1 .8 1.6L15 13.2V19a1 1 0 0 1-1.45.9l-4-2A1 1 0 0 1 9 17v-3.8L3.2 4.6A1 1 0 0 1 3 4z"/></svg>
              Filtro
            </h3>
          </div>

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
                  console.log("📝 Input:", e.target.value);
                  setSymbolQuery(e.target.value.toUpperCase());
                  setSelectedSymbol('');
                  setHighlightedIndex(-1);
                }}
                onKeyDown={(e) => {
                  if (symbolSuggestions.length === 0) return;

                  if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    setHighlightedIndex((prevIndex) => Math.min(prevIndex + 1, symbolSuggestions.length - 1));
                  } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    setHighlightedIndex((prevIndex) => Math.max(prevIndex - 1, -1));
                  } else if (e.key === 'Enter') {
                    if (highlightedIndex !== -1) {
                      setSelectedSymbol(symbolSuggestions[highlightedIndex]);
                      setSymbolQuery(symbolSuggestions[highlightedIndex]);
                      setSymbolSuggestions([]);
                      setHighlightedIndex(-1);
                    }
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

            {/* Fecha (opcional / futura integración) */}
            {/* <div>
              <label className="block text-sm font-medium text-muted mb-1">Fecha</label>
              <input
                type="date"
                className="w-full p-2 border border-blue-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-400"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
              />
            </div> */}

            {/* Botones */}
            <div className="flex gap-2 pt-7">
              <button
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-md transition"
                onClick={handleClick}
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="white"><path d="M3 4a1 1 0 0 1 1-1h16a1 1 0 0 1 .8 1.6L15 13.2V19a1 1 0 0 1-1.45.9l-4-2A1 1 0 0 1 9 17v-3.8L3.2 4.6A1 1 0 0 1 3 4z"/></svg>
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

}

export default StrategyButton;