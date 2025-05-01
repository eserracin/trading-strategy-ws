import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const useStrategyStore = create(
    devtools((set, get) => ({
        activeStrategies: {},
        selectedSymbol: null,
        selectedStrategy: null,
        selectedTimeframe: null,
        lastActivated: null,

        setSelectedStrategy: (symbol, strategy, timeframe) => set({ selectedSymbol: symbol, selectedStrategy: strategy, selectedTimeframe: timeframe }),
        setLastActivated: (symbol, strategy) => set({ symbol, strategy }),  

        // Activar una estrategia
        activateStrategy: (symbol, strategyName) => {
            const key = symbol+strategyName;
            const currentStrategy = get().activeStrategies[key];
            if (currentStrategy) return;

            const update = {
                ...get().activeStrategies, 
                [key]: {
                    symbol,
                    strategyName,
                    socketEnabled: true,
                    status: 'loading'
                }  
            };


            set({ activeStrategies: update});
        },

        // Actualizar el estado de una estrategia
        updateStrategyStatus: (symbol, strategyName, status) => {
            const key = symbol+strategyName;
            const update = { ...get().activeStrategies };
            if (update[key]) {
                update[key].status = status;
                set({ activeStrategies: update });
            }
        },

        // Desactivar una estrategia
        deactivateStrategy: (symbol, strategyName) => {

            const key = symbol+strategyName;

            const update = { ...get().activeStrategies };
            delete update[key];

            set({ activeStrategies: update });
        },

        // Limpiar todas las estrategias activas
        clearAllStrategies: () => {
            set({ activeStrategies: {} });
        }

    }))
);

export default useStrategyStore;