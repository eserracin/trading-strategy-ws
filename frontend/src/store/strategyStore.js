import { create } from 'zustand';

const useStrategyStore = create((set, get) => ({
    activeStrategies: {},
    socketEnabled: false,

    selectedSymbol: null,
    selectedStrategy: null,
    setSelectedStrategy: (symbol, strategy) => set({ selectedSymbol: symbol, selectedStrategy: strategy }),

    // Activar una estrategia
    activateStrategy: (symbol, strategyName) => {
        const update = { ...get().activeStrategies, [symbol]: strategyName  };
        set({ activeStrategies: update, socketEnabled: true  });
    },

    // Desactivar una estrategia
    deactivateStrategy: (symbol) => {
        const update = { ...get().activeStrategies };
        delete update[symbol];

        const stillHasStrategies = Object.keys(update).length > 0;
        set({ activeStrategies: update, socketEnabled: stillHasStrategies });
    },

    // Limpiar todas las estrategias activas
    clearAllStrategies: () => {
        set({ activeStrategies: {} });
    }
}));

export default useStrategyStore;