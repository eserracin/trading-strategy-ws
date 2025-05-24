# src/core/trade_manager/trade_executor.py
from binance.client import Client
from binance.enums import (
    SIDE_BUY, SIDE_SELL, 
    FUTURE_ORDER_TYPE_STOP_MARKET, FUTURE_ORDER_TYPE_MARKET, FUTURE_ORDER_TYPE_LIMIT,
    TIME_IN_FORCE_GTC)
from config.settings import SYMBOL
import logging
import decimal
import asyncio

class TradeExecutor:
    def __init__(self, client: Client, symbol: str = SYMBOL, logger: logging.Logger = None, isMock: bool = False):
        self.client = client
        self.symbol = symbol
        self.logger = logger
        self.isMock = isMock
        self.symbol_info = None
        self.price_filter = None
        self.lot_size_filter = None

        if not self.isMock:
            self._load_symbol_info()

    def _load_symbol_info(self):
        """Carga y parsea la información del símbolo para filtros de precio y lote."""
        try:
            exchange_info = self.client.futures_exchange_info()
            for s_info in exchange_info['symbols']:
                if s_info['symbol'] == self.symbol:
                    self.symbol_info = s_info
                    break
            
            if not self.symbol_info:
                self.logger.error(f"No se pudo encontrar información para el símbolo {self.symbol}")
                return

            for f in self.symbol_info['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    self.price_filter = f
                elif f['filterType'] == 'LOT_SIZE':
                    self.lot_size_filter = f
            
            if not self.price_filter or not self.lot_size_filter:
                self.logger.error(f"No se pudieron encontrar PRICE_FILTER o LOT_SIZE para {self.symbol}")

        except Exception as e:
            self.logger.error(f"Error cargando información del símbolo {self.symbol}: {e}")

    def _format_price(self, price: float) -> str:
        if self.isMock or not self.price_filter:
            return str(price) # Mock o sin info, devuelve como string
        
        # tickSize define el incremento válido para el precio
        # El precio debe ser múltiplo de tickSize
        tick_size = decimal.Decimal(self.price_filter['tickSize'])
        price_decimal = decimal.Decimal(str(price))
        
        # Redondear el precio al múltiplo más cercano de tick_size
        # (price / tick_size) * tick_size
        formatted_price_decimal = (price_decimal // tick_size) * tick_size # Trunca hacia tick_size
        
        # Asegurar el número correcto de decimales según tick_size
        precision = abs(tick_size.as_tuple().exponent)
        return f"{formatted_price_decimal:.{precision}f}"
    
    def _format_quantity(self, quantity: float) -> str:
        if self.isMock or not self.lot_size_filter:
            # Para mock, permitir más flexibilidad, o definir mock step_size
            if self.isMock: return str(round(quantity, 8)) # Permitir más decimales en mock
            return str(quantity)

        # stepSize define la precisión de la cantidad
        step_size = decimal.Decimal(self.lot_size_filter['stepSize'])
        quantity_decimal = decimal.Decimal(str(quantity))

        # La cantidad debe ser un múltiplo de step_size
        # (quantity // step_size) * step_size asegura que se trunca al múltiplo válido más bajo
        formatted_quantity_decimal = (quantity_decimal // step_size) * step_size
        
        # Asegurar el número correcto de decimales según step_size
        precision = abs(step_size.as_tuple().exponent)
        return f"{formatted_quantity_decimal:.{precision}f}"
    
    async def _execute_client_call(self, method_name, **kwargs):
        """Ejecuta una llamada al cliente de Binance en un hilo separado."""
        method = getattr(self.client, method_name)
        return await asyncio.to_thread(method, **kwargs)


    async def place_order(self, mode: str, entry_price: float, sl_price: float, tp_price: float, quantity: float):
        """
        Place a market order to buy or sell a specified quantity of the asset.

        :param mode: 'buy' or 'sell'
        :param entry_price: Entry price for the order
        :param sl_price: Stop loss price
        :param tp_price: Take profit price
        :param quantity: Quantity of the asset to buy/sell
        """
        self.logger.info(f"Attempting to place order: mode={mode}, symbol={self.symbol}, qty={quantity}, sl={sl_price}, tp={tp_price}")

        if self.isMock:

            self.logger.info("--- MOCK MODE ENABLED ---")
            # Simular datos de respuesta para mock
            mock_entry_side = SIDE_BUY if mode.upper() == 'LONG' else SIDE_SELL
            mock_sl_tp_side = SIDE_SELL if mode.upper() == 'LONG' else SIDE_BUY
            
            # Usar precios y cantidades formateadas (simulando)
            formatted_quantity = self._format_quantity(quantity)
            formatted_sl_price = self._format_price(sl_price)
            formatted_tp_price = self._format_price(tp_price)

            order_id_counter = abs(hash(f"{self.symbol}{mode}{quantity}{sl_price}{tp_price}")) % 100000                


            mock_order = {
                "orderId": order_id_counter,
                "symbol": self.symbol,
                "side": mock_entry_side,
                "type": FUTURE_ORDER_TYPE_MARKET,
                "status": "FILLED",
                "price": self._format_price(entry_price),
                "avgPrice": self._format_price(entry_price * 1.0005),
                "origQty": formatted_quantity,
                "executedQty": formatted_quantity,
                "timestamp": int(asyncio.get_running_loop().time() * 1000)
            }
            mock_sl_order = {
                "orderId": order_id_counter + 1,
                "symbol": self.symbol,
                "side": mock_sl_tp_side,
                "type": FUTURE_ORDER_TYPE_STOP_MARKET,
                "stopPrice": formatted_sl_price,
                "origQty": formatted_quantity,
                "status": "NEW",
                "reduceOnly": True,
                "timestamp": int(asyncio.get_running_loop().time() * 1000) + 10
            }
            mock_tp_order = {
                "orderId": order_id_counter + 2,
                "symbol": self.symbol,
                "side": mock_sl_tp_side,
                "type": FUTURE_ORDER_TYPE_LIMIT,
                "price": formatted_tp_price,
                "stopPrice": "0",
                "origQty": formatted_quantity,
                "status": "NEW",
                "timeInForce": TIME_IN_FORCE_GTC,
                "reduceOnly": True,
                "timestamp": int(asyncio.get_running_loop().time() * 1000) + 20
            }
            self.logger.info(f"Mock Entry Order: {mock_order}")
            self.logger.info(f"Mock SL Order: {mock_sl_order}")
            self.logger.info(f"Mock TP Order: {mock_tp_order}")
            return {'order': mock_order, 'sl_order': mock_sl_order, 'tp_order': mock_tp_order}


        try:
            if not self.symbol_info or not self.price_filter or not self.lot_size_filter:
                self.logger.error(f"Información del símbolo {self.symbol} no cargada. No se puede colocar la orden.")
                return 
                
            # Formatear cantidad y precios según las reglas del símbolo
            formatted_quantity = self._format_quantity(quantity)
            formatted_sl_price = self._format_price(sl_price)
            formatted_tp_price = self._format_price(tp_price)

            entry_side = SIDE_BUY if mode.upper() == 'LONG' else SIDE_SELL
            sl_tp_side = SIDE_SELL if mode.upper() == 'LONG' else SIDE_BUY

            self.logger.info(f"Placing Futures MARKET Order: Symbol={self.symbol}, Side={entry_side}, Quantity={formatted_quantity}")
            entry_order_response = await self._execute_client_call(
                'futures_create_order',
                symbol=self.symbol,
                side=entry_side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=formatted_quantity
                # timeInForce no es necesario para MARKET, pero no daña. Se puede omitir.
            )
            self.logger.info(f"Futures MARKET Order Response: {entry_order_response}")

            executed_quantity = entry_order_response.get('executedQty', formatted_quantity)

            # Colocar Orden Stop Loss (STOP_MARKET)
            self.logger.info(f"Placing SL Order (STOP_MARKET): Symbol={self.symbol}, Side={sl_tp_side}, StopPrice={formatted_sl_price}, Quantity={executed_quantity}, ReduceOnly=True")
            sl_order_response = await self._execute_client_call(
                'futures_create_order',
                symbol=self.symbol,
                side=sl_tp_side,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                stopPrice=formatted_sl_price,
                quantity=executed_quantity,
                reduceOnly=True,
                timeInForce=TIME_IN_FORCE_GTC
            )
            self.logger.info(f"SL Order (STOP_MARKET) Response: {sl_order_response}")


            # Colocar Orden Take Profit (LIMIT)
            self.logger.info(f"Placing TP Order (LIMIT): Symbol={self.symbol}, Side={sl_tp_side}, Price={formatted_tp_price}, Quantity={executed_quantity}, ReduceOnly=True")
            tp_order_response = await self._execute_client_call(
                'futures_create_order',
                symbol=self.symbol,
                side=sl_tp_side,
                type=FUTURE_ORDER_TYPE_LIMIT,
                price=formatted_tp_price,
                quantity=executed_quantity, # Usar la cantidad ejecutada de la orden de entrada
                timeInForce=TIME_IN_FORCE_GTC,
                reduceOnly=True # MUY IMPORTANTE para TP
            )
            self.logger.info(f"TP Order (LIMIT) Response: {tp_order_response}")

            return {
                'order': entry_order_response,
                'sl_order': sl_order_response,
                'tp_order': tp_order_response
            }

        except Exception as e:
            self.logger.error(f"Error placing order sequence for {self.symbol}: {e}", exc_info=True)
            return 
        
    async def cancel_order_async(self, order_id: int, is_client_order_id: bool = False):
        """Cancela una orden específica."""
        try:
            self.logger.info(f"Attempting to cancel order: order_id={order_id}, symbol={self.symbol}")
            params = {'symbol': self.symbol}
            if is_client_order_id:
                params['origClientOrderId'] = str(order_id)
            else:
                params['orderId'] = order_id
            
            response = await self._execute_client_call('futures_cancel_order', **params)
            self.logger.info(f"Cancel order response for {order_id}: {response}")
            return response
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id} for {self.symbol}: {e}", exc_info=True)
            return None
        
    async def get_open_orders_async(self):
        """Obtiene todas las órdenes abiertas para el símbolo actual."""
        try:
            self.logger.debug(f"Fetching open orders for {self.symbol}")
            open_orders = await self._execute_client_call('futures_get_open_orders', symbol=self.symbol)
            return open_orders
        except Exception as e:
            self.logger.error(f"Error fetching open orders for {self.symbol}: {e}", exc_info=True)
            return []

    async def cancel_all_open_orders_async(self):
        """Cancela todas las órdenes abiertas para el símbolo actual."""
        try:
            self.logger.info(f"Attempting to cancel all open orders for {self.symbol}")
            response = await self._execute_client_call('futures_cancel_all_open_orders', symbol=self.symbol)
            self.logger.info(f"Cancel all open orders response for {self.symbol}: {response}")
            # La respuesta a futures_cancel_all_open_orders puede ser un success code, no una lista de órdenes.
            # El código 200 con un JSON {"code": 200, "msg": "The operation has been done."} es común.
            if isinstance(response, dict) and response.get("code") == 200:
                return True
            # Si la API devuelve una lista de órdenes canceladas (algunas implementaciones lo hacen)
            if isinstance(response, list):
                return True # Asumir éxito si devuelve una lista (incluso vacía)
            return response # Devolver la respuesta para inspección
        except Exception as e:
            self.logger.error(f"Error cancelling all open orders for {self.symbol}: {e}", exc_info=True)
            return False