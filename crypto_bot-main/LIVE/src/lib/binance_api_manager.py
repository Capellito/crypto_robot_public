from binance.client import Client
from binance.enums import *

from src.lib.websocket_manager import WebSocketManager
import src.global_variables as global_variables
import src.lib.utils as utils
import pandas as pd
import requests
import time

import json
import websocket

class BinanceApiManager():

    # INIT
    def __init__(self, api_key=global_variables.api_key, api_secret=global_variables.api_secret):
        self.client = Client(api_key, api_secret)
        self.ws_manager = WebSocketManager()

        self.last_request_weight = 0

        self.symbol = ""
        self.pair = ""
        self.token_quantity = 0
        self.crypto_price = 0
        self.take_profit = 0
        self.stop_loss = 0
        self.stop_loss_limit = 0
        self.open_orders = []
        self.quantity_resolution = 0
        self.price_resolution = 0
        self.daily_winners = []
    
    # SETTER
    def set_symbol(self, symbol):
        self.symbol = symbol
    
    def set_pair(self, pair):
        self.pair = pair

    def set_token_quantity(self, token_quantity):
        self.token_quantity = token_quantity
        
    def set_crypto_price(self, crypto_price):
        self.crypto_price = crypto_price

    def set_take_profit(self, take_profit):
        self.take_profit = take_profit

    def set_stop_loss(self, stop_loss):
        self.stop_loss = stop_loss

    def set_stop_loss_limit(self, stop_loss_limit):
        self.stop_loss_limit = stop_loss_limit

    def set_open_orders(self, open_orders):
        self.open_orders = open_orders

    def set_quantity_resolution(self, quantity_resolution):
        self.quantity_resolution = quantity_resolution

    def set_price_resolution(self, price_resolution):
        self.price_resolution = price_resolution

    def set_daily_winners(self, daily_winners):
        self.daily_winners = daily_winners

    # FUNCTIONS
    def check_request_weight(self):
        # On recupere le poids de la dernière requête
        self.last_request_weight = self.client.response.headers.get('x-mbx-used-weight-1m')

        # On vérifie le nombre de requête pour eviter le ban
        current_time = int(time.time())
        remaining_seconds = 60 - (current_time % 60)
        if int(self.last_request_weight) >= 1050:
            utils.debug(3, "BINANCE API MANAGER -- CHECK REQUEST WEIGHT -- Too much request weight used ({0}), waiting for the end of the minute...".format(self.last_request_weight))
            time.sleep(remaining_seconds)
            self.last_request_weight = 0

        utils.debug(4, "BINANCE API MANAGER -- CHECK REQUEST WEIGHT -- Number of request : {0}".format(self.last_request_weight))

    def sell_market(self, pair=None, token_quantity=None):        
        if pair is None:
            pair = self.pair
        if token_quantity is None:
            token_quantity = self.token_quantity
        try:
            order = self.client.order_market_sell(
                symbol=pair, 
                quantity=token_quantity)
        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- SELL MARKET - symbol: {0}, quantity: {1}".format(pair, token_quantity))
            utils.debug(2, str(e))
            return False
        else:
            utils.debug(2, "BINANCE API MANAGER -- SELL MARKET -- {0} {1}".format(token_quantity, pair))
            return True

    def buy_market(self, pair=None, token_quantity=None):
        if pair is None:
            pair = self.pair
        if token_quantity is None:
            token_quantity = self.token_quantity
        try:
            order = self.client.order_market_buy(
                symbol=pair, 
                quantity=token_quantity)
        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- BUY MARKET - symbol: {0}, quantity: {1}".format(pair, token_quantity))
            utils.debug(2, str(e))
            return False
        else:
            utils.debug(2, "BINANCE API MANAGER -- BUY MARKET -- {0} {1}".format(token_quantity, pair))
            return True

    def create_OCO_order(self, pair=None, token_quantity=None, take_profit=None, stop_loss=None, stop_loss_limit=None):
        if pair is None:
            pair = self.pair
        if token_quantity is None:
            token_quantity = self.token_quantity
        if take_profit is None:
            take_profit = self.take_profit
        if stop_loss is None:
            stop_loss = self.stop_loss
        if stop_loss_limit is None:
            stop_loss_limit = self.stop_loss_limit
        try:
            order= self.client.order_oco_sell(
                symbol= pair,                                            
                quantity= token_quantity,                                            
                price= take_profit,                                            
                stopPrice= stop_loss,                                            
                stopLimitPrice= stop_loss_limit,                                        
                stopLimitTimeInForce= 'GTC')
        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- CREATE EXIT ORDER - symbol: {0}, quantity: {1}, takeProfit: {2}, stopLoss: {3}, stopLossLimit: {4}".format(pair, token_quantity, take_profit, stop_loss, stop_loss_limit))     
            utils.debug(3, str(e))
            return False
        else:
            utils.debug(2, "BINANCE API MANAGER -- CREATE EXIT ORDER - Eco order placed {0} {1} | TP: {2}, SL: {3} SLL: {4}".format(token_quantity, pair, take_profit, stop_loss, stop_loss_limit))  
            return True

    def get_resolutions(self, pair=None):
        if pair is None:
            pair = self.pair
        try:
            info = self.client.get_symbol_info(pair)

            self.quantity_resolution = float(info['filters'][1]['minQty'])

            self.price_resolution = float(info['filters'][0]['minPrice'])
        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- GET RESOLUTION")
            utils.debug(3, str(e))
        else:
            utils.debug(3, "BINANCE API MANAGER -- GET RESOLUTIONS -- {0} Quantity: {1} | Price: {2}".format(pair, self.quantity_resolution, self.price_resolution))

            return self.quantity_resolution, self.price_resolution

    def get_crypto_price(self, pair=None):
        if pair is None:
            pair = self.pair
        try:
            url = "https://api.binance.com/api/v3/ticker/price?symbol={0}".format(str(pair))
            response = requests.get(url)

            data = response.json()
            self.crypto_price = data["price"]
            self.crypto_price = float(self.crypto_price)
        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- GET CRYPTO PRICE")
            utils.debug(3, str(e))
        else:
            utils.debug(3, "BINANCE API MANAGER -- GET CRYPTO PRICE {0}: {1}$".format(pair, self.crypto_price))

            return self.crypto_price

    def get_ws_crypto_price(self, pair=None):
        if pair is None:
            pair = self.pair
        try:
            self.ws_manager.stream_url = '{"method": "SUBSCRIBE", "params": ["' + str(pair).lower() + '@ticker"], "id": 1}'
            self.ws_manager.run()
            if len(str(self.ws_manager.response)) > 100:
                self.crypto_price = float(self.ws_manager.response["c"])
        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- GET WS CRYPTO PRICE")
            utils.debug(3, str(e))
            return False
        else:
            utils.debug(3, "BINANCE API MANAGER --  GET WS CRYPTO PRICE {0}: {1}".format(pair, self.crypto_price))
            return float(self.ws_manager.response["c"])

    def get_token_quantity(self, symbol=None):
        if symbol is None:
            symbol = self.symbol
        try:
            balance = self.client.get_asset_balance(asset=symbol)

            self.token_quantity = float(balance["free"])

        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- GET TOKEN QUANTITY")
            utils.debug(3, str(e))
            return False
        else:
            utils.debug(4, "BINANCE API MANAGER -- Get token quantity {0}: {1}$".format(symbol, self.token_quantity))
            return self.token_quantity

    def get_open_orders(self):
        try:
            self.check_request_weight()
            self.open_orders = self.client.get_open_orders()
        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- GET OPEN ORDER")
            utils.debug(3, str(e))
        else:
            return self.open_orders

    def cancel_open_order(self, order):
        try:
            self.check_request_weight()
            self.client.cancel_order(symbol=order["symbol"], orderId=order["orderId"])
        except Exception as e:
            utils.debug(2, "BINANCE API MANAGER -- ERROR -- CANCEL ORDER")
            utils.debug(3, str(e))
        else:
            self.pair = order["symbol"]
            utils.debug(2, "BINANCE API MANAGER -- CANCEL OPEN ORDER -- Order canceled")

    def cancel_all_open_orders(self):
        for open_order in self.open_orders:
            self.cancel_open_order(order=open_order)

    def is_crypto_tradable(self, pair=None):
        if pair is None:
            pair = self.pair
        try:
            self.check_request_weight()
            df = self.client.get_symbol_info(symbol=pair)
        except Exception as e:
            utils.debug(3, 'BINANCE API MANAGER -- ERROR -- IS CRYPTO TRADABLE')
            utils.debug(3, str(e))
        else:
            if df is None:
                return False
            if (df['status'] == "TRADING"):
                return True
            
        return False

    def get_daily_winner(self):
        try:
            # on recupere toute les crypto et info des 24h
            self.check_request_weight()
            tickers = self.client.get_ticker()
        except Exception as e:
            utils.debug(3, 'BINANCE API MANAGER -- ERROR -- GET DAILY WINNER')
            utils.debug(3, str(e))
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(tickers)
            
            df["priceChangePercent"] = pd.to_numeric( df["priceChangePercent"])
            
            # on ne veut que les pair de la currency trader
            df['indice'] = df['symbol'].str.split(global_variables.trade_currency).str[1]
            df = df[df['indice']=='']
            
            # On trie par winner
            df = df.sort_values(by=["priceChangePercent"], ascending=False)
            
            del df['priceChange']
            df.drop(df[df["priceChangePercent"] <= 8].index, inplace = True)
            
        return df

    def get_candle_stick(self, pair, interval, duration):
        try:
            self.check_request_weight()
            klinesT = self.client.get_historical_klines(pair, interval, duration)
        except Exception as e:
            utils.debug(3, "BINANCE API MANAGER -- ERROR -- GET CANDLE STICK")
            utils.debug(3, str(e))
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(klinesT, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore' ])
            
            del df['close_time']
            del df['quote_av']
            del df['trades']
            del df['tb_base_av']
            del df['tb_quote_av']
            
            df['close'] = pd.to_numeric(df['close'])	     	    
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['open'] = pd.to_numeric(df['open'])	
        
            df = df.set_index(df['timestamp'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.index = pd.to_datetime(df.index, unit='ms')        
            
        return df
