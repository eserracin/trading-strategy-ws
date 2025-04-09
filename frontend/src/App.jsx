import './App.css'
import StrategyButton from './components/StrategyButton';
import ActiveSymbolTable from './components/ActiveSymbolTable';
import TradeTable from './components/TradeTable';
import LiveEvents from './components/LiveEvents';

function App() {
  
  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-3xl font-bold text-center text-blue-700">📊 Trading Dashboard</h1>  

      <div className="text-balance bg-primary text-white p-4 rounded">
         debería aplicar clases nuevas de Tailwind v4
      </div>

      <div className="mt-10 flex flex-col items-center">
        <StrategyButton />
        <ActiveSymbolTable activeSymbols={[]} />
        {/* <LiveEvents />
        <TradeTable /> */}
      </div>
    </div>
  )
}

export default App
