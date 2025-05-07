// utils/keyBuilder.js

/**
 * Genera una clave única compuesta para una estrategia activa.
 * Formato recomendado: SYMBOL::STRATEGY::TF
 *
 * @param {string} symbol 
 * @param {string} strategy 
 * @param {string} timeframe 
 * @returns {string}
 */
export const buildStrategyKey = (symbol, strategy, timeframe) => {
    return `${symbol}::${strategy}::${timeframe}`;
  };
  