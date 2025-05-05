// src/components/ActiveSymbolTable/ActiveSymbolRow.jsx
import React, { useEffect } from 'react';
import { useCandleStream } from '../../hooks/useCandleStream';

/**
 * Componente que se encarga de suscribirse al stream de una clave específica y
 * ejecutar una función cuando llegan nuevas velas. Se debe envolver alrededor del render de fila.
 *
 * @param {string} keyId - Clave única SYMBOL::STRATEGY::TF
 * @param {function} onCandle - Callback para manejar los datos de la vela
 * @param {React.ReactNode} children - Fila a renderizar
 */
const ActiveSymbolRow = ({ keyId, onCandle, children }) => {
  useCandleStream(keyId, (data) => {
    try {
      if (typeof data !== 'object' || data === null) throw new Error('Dato no válido');
      onCandle(data);
    } catch (error) {
      console.error('🔴 Error en handler de ActiveSymbolRow:', error);
    }
  });

  return children;
};

export default ActiveSymbolRow;
