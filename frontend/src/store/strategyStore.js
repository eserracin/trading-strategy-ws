// src/store/strategyStore.js
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const useStrategyStore = create(
  devtools((set, get) => ({
    activeStrategies: {},
    selectedSymbol: null,
    selectedStrategy: null,
    selectedTimeframe: null,

    setSelectedStrategy: (symbol, strategy, timeframe) =>
      set({ selectedSymbol: symbol, selectedStrategy: strategy, selectedTimeframe: timeframe }),

    activateStrategy: (symbol, strategyName, timeframe) => {
      const key = symbol + strategyName + timeframe;
      const current = get().activeStrategies[key];
      if (current) return;

      const updated = {
        ...get().activeStrategies,
        [key]: {
          symbol,
          strategyName,
          timeframe,
          status: 'loading',
        },
      };

      set({ activeStrategies: updated });
    },

    updateStrategyStatus: (key, status) => {
      // const key = symbol + strategyName + timeframe;
      const update = { ...get().activeStrategies };
      if (update[key]) {
        update[key].status = status;
        set({ activeStrategies: update });
      }
    },

    deactivateStrategy: (symbol, strategyName, timeframe) => {
      const key = symbol + strategyName + timeframe;
      const update = { ...get().activeStrategies };
      delete update[key];
      set({ activeStrategies: update });
    },

    clearAllStrategies: () => {
      set({ activeStrategies: {} });
    },
  }))
);

export default useStrategyStore;