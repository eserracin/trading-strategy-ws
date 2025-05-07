// tests/ActiveSymbolTable.test.jsx
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { vi } from 'vitest'
import ActiveSymbolTable from '../src/components/ActiveSymbolTable/ActiveSymbolTable'
import * as ws from '../src/services/ws'
import useStrategyStore from '../src/store/strategyStore'

// Mocks
vi.mock('../src/services/ws')

describe('ActiveSymbolTable - WebSocket Integration', () => {
  beforeEach(() => {
    // Mock de estrategias activas
    useStrategyStore.setState({
      activeStrategies: {
        'BTCUSDT::SCALPING::15m': {
          symbol: 'BTCUSDT',
          strategyName: 'SCALPING',
          timeframe: '15m'
        }
      },
      deactivateStrategy: vi.fn(),
      updateStrategyStatus: vi.fn(),
    });

    // Reset y mock de funciones WebSocket
    ws.connectWS.mockImplementation(() => {})
    ws.suscribeToWS.mockImplementation((url, handler) => {
      // Simula que llega una vela después de 500ms
      setTimeout(() => {
        handler({
          tipo: 'candle',
          open: 10000,
          high: 10100,
          low: 9900,
          close: 10050,
          volume: 123.45,
          interval: '15m',
          open_time: Date.now() - 60000,
          close_time: Date.now() + 60000
        });
      }, 500);
    });
    ws.unsubscribeFromWS.mockImplementation(() => {})
    ws.closeWS.mockImplementation(() => {})
  });

  it('debe mostrar datos de la vela cuando llegan por WebSocket', async () => {
    render(<ActiveSymbolTable />)

    // Verifica que primero aparece el spinner de carga
    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    // Espera a que se renderice el precio '10050'
    await waitFor(() => {
      expect(screen.getByText('10050')).toBeInTheDocument()
    })

    // Verifica también que el símbolo aparece
    expect(screen.getByText('BTCUSDT')).toBeInTheDocument()
    expect(screen.getByText('SCALPING')).toBeInTheDocument()
    expect(screen.getByText('15m')).toBeInTheDocument()
  })
})
