# src/core/trade_manager/trade_executor.py
from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, TIME_IN_FORCE_GTC
from config.settings import SYMBOL
import logging

class TradeExecutor:
    def __init__(self, client: Client, symbol: str = SYMBOL, logger: logging.Logger = None, isMock: bool = False):
        self.client = client
        self.symbol = symbol
        self.logger = logger
        self.isMock = isMock

    def place_order(self, mode: str, entry_price: float, sl_price: float, tp_price: float, quantity: float):
        """
        Place a market order to buy or sell a specified quantity of the asset.

        :param mode: 'buy' or 'sell'
        :param entry_price: Entry price for the order
        :param sl_price: Stop loss price
        :param tp_price: Take profit price
        :param quantity: Quantity of the asset to buy/sell
        """
        try:
            if self.isMock:
                    order = {
                        "orderId": 100001,
                        "symbol": "BTCUSDT",
                        "side": "BUY",  # o "SELL" si es short
                        "type": "MARKET",
                        "status": "FILLED",
                        "price": "60000.00",
                        "executedQty": "0.01",
                        "timestamp": 1713195800000
                    }
                    sl_order = {
                        "orderId": 100002,
                        "symbol": "BTCUSDT",
                        "side": "SELL",
                        "type": "STOP_MARKET",
                        "stopPrice": "59800.00",
                        "status": "NEW",
                        "timestamp": 1713195810000
                    }

                    tp_order = {
                        "orderId": 100003,
                        "symbol": "BTCUSDT",
                        "side": "SELL",
                        "type": "LIMIT",
                        "price": "60500.00",
                        "status": "NEW",
                        "timestamp": 1713195815000
                    }
            else:

                side = SIDE_BUY if mode.upper() == 'LONG' else SIDE_SELL

                order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side=side,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity,
                    timeInForce=TIME_IN_FORCE_GTC
                )
                self.logger.info(f"Order placed: {order}")

                # Crear ordenes de stop loss y take profit (usando OCO o por separado según Binance Futures API)
                sl_side = SIDE_SELL if mode.upper() == 'LONG' else SIDE_BUY
                tp_side = SIDE_SELL if mode.upper() == 'SHORT' else SIDE_BUY

                # SL
                sl_order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side=sl_side,
                    type='STOP_MARKET',
                    stopPrice=sl_price,
                    timeInForce=TIME_IN_FORCE_GTC
                )
                self.logger.info(f"Stop Loss order placed: {sl_order}")

                # TP
                tp_order = self.client.futures_create_order(
                    symbol=self.symbol,
                    side=tp_side,
                    type='LIMIT',
                    price=round(tp_price, 2),
                    quantity=round(quantity, 3),
                    timeInForce=TIME_IN_FORCE_GTC,
                    reduceOnly=True
                )
                self.logger.info(f"Take Profit order placed: {tp_order}")

            return  {
                'order': order,
                'sl_order': sl_order,
                'tp_order': tp_order
            }

        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            return None