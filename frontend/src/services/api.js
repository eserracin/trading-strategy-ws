const BASE_URL = 'http://localhost:8000/api';

export const fetchStrategies = async () => {
  try {
    const response = await fetch(`${BASE_URL}/estrategias`)
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    console.log(`fetched strategies: ${JSON.stringify(data)}`)
    return data;
  } catch (error) {
    console.error('Error fetching strategies:', error);
    throw error;
  }
}

export const executeStrategy = async (symbol, strategy, test = true) => {
    try {
        const res = await fetch(`${BASE_URL}/ejecutar-estrategia`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ symbol, strategy, test }),
      })
  
      if (!res.ok) {
        throw new Error('Network response was not ok');
      }
  
      const data = await res.json();
      return data;
    } catch (error) {
      console.error('Error executing strategy:', error);
      throw error;
    }
  }

export const fetchTrades = async () => {
  try {
    const response = await fetch(`${BASE_URL}/operaciones`)
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching trades:', error);
    throw error;
  }
}

export const searchSymbols = async (query) => {
  try {
    const response = await fetch(`${BASE_URL}/symbols?q=${query}`)
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error searching symbols:', error);
    throw error;
  }
}

export const getMarketData = async (symbol) => {
  try {
    const response = await fetch(`${BASE_URL}/market-data/${symbol}`)
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching market data:', error);
    throw error;
  }
}