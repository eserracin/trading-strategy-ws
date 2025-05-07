// src/services/api.js
import axiosClient  from "./axiosClient";


export const fetchStrategies = async () => {
  try {
    const response = await axiosClient.get('/strategy/listar-estrategias');
    return response.data.data;
  } catch (error) {
    console.error('Error fetching strategies:', error);
    throw error;
  }
}

export const startStrategy = async (symbol, strategy, timeframe, test = true) => {
  try {
    const response = await axiosClient.post('/strategy/ejecutar-estrategia', {
      symbol,
      strategy,
      timeframe,
      test,
    });
    return response.data.data;
  } catch (error) {
    console.error('Error executing strategy:', error);
    throw error;
  }
}

export const stopStrategy = async (symbol, strategy, timeframe) => {
  try {
    const response = await axiosClient.post('/strategy/detener-estrategia', {
      symbol,
      strategy,
      timeframe,
    });
    return response.data.data;
  } catch (error) {
    console.error('Error stopping strategy:', error);
    throw error;
  }
}

export const createActiveSymbol = async (symbol, strategy) => {
  try {
    const response = await axiosClient.post('/symbol/crear-simbolo-activo', {
      symbol,
      strategy,
    });
    return response.data;
  } catch (error) {
    console.error('Error creating active symbol:', error);
    throw error;
  }
}

export const fetchTrades = async () => {
  try {
    const response = await axiosClient.get('/operaciones');
    return response.data;
  } catch (error) {
    console.error('Error fetching trades:', error);
    throw error;
  }
}

export const searchSymbols = async (query) => {
  try {
    const response = await axiosClient.get(`/symbol/obtener-simbolos?q=${query}`);
    return response.data.data;
  } catch (error) {
    console.error('Error searching symbols:', error);
    throw error;
  }
}

export const loginUser = async (email, password) => {
  try {
    const response = await axiosClient.post('/auth/iniciar-sesion', {
      email,
      password,
    });
    return response.data;
  } catch (error) {
    console.error('Error logging in:', error);
    throw error;
  }
}

export const registerUser = async (email, password) => {
  try {
    const response = await axiosClient.post('/auth/registrar', {
      email,
      password,
    });
    return response.data;
  } catch (error) {
    console.error('Error registering:', error);
    throw error;
  }
}