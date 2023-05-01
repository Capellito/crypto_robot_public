from datetime import datetime, timedelta
from binance.client import Client

import src.global_variables as gv
import src.lib.utils as utils
from src.lib.binance_api_manager import BinanceApiManager
from src.lib.telegram_manager import TelegramManager

from threading import Event

import pandas as pd
import sys

class TradingBot:
    
    def __init__(self, take_profit_ratio, stop_loss_ratio, candle_length_limit, debug, live_or_not, event=False):        
        self.candle_length_limit = candle_length_limit
        self.take_profit_ratio = take_profit_ratio
        self.stop_loss_ratio = stop_loss_ratio
        self.debug = debug
        self.live = live_or_not
        self.event = event
        self.binance_api_manager = BinanceApiManager(api_key=gv.api_key, api_secret=gv.api_secret)
        self.telegram_manager = TelegramManager(gv.telegram_token)
        self.restore_variable_for_csv()
        self.set_global_variable()

    def set_global_variable(self):
        gv.debug = self.debug
        gv.take_profit_ratio = self.take_profit_ratio
        gv.stop_loss_ratio = self.stop_loss_ratio
        gv.candle_length_limit = self.candle_length_limit

    def restore_variable_for_csv(self):
        self.in_position = False
        self.crypto_in_position = None
        self.pair = None
        self.take_profit = None
        self.stop_loss = None
        self.busd_balance = None
        # csv
        self.time = None
        self.candle_length = None
        self.enter_price = None
        self.result = None
        self.open = None
        self.day_percent = None
        self.time_in_trade = None
        self.tab_prices = []
        self.last24h = []
        self.tab_times = [] 

    def cancel_open_orders(self):
        position = self.binance_api_manager

        # On recupère la liste des ordres ouverts
        position.get_open_orders()

        # Si il y a des ordres ouverts
        if not position.open_orders == []:
            # On les annules
            position.cancel_all_open_orders()

            # On recupere le symbole de la crypto
            position.set_symbol(str(position.pair).split(gv.trade_currency)[0])

            # On recupere la quantité de token
            position.set_token_quantity(position.get_token_quantity())

            # On vend la crypto au prix du marché
            position.sell_market()

    def close_position(self, result):
        self.result = result
        # On recupere le resultat et la durée du trade
        self.time_in_trade = self.time - (datetime.now())

        # On recupere les 24 dernières bougie 1h
        df_last24h = self.binance_api_manager.get_candle_stick(self.pair, Client.KLINE_INTERVAL_1HOUR, '24HOUR')        
        if not df_last24h.empty:
            for index, row in df_last24h.iterrows():
                self.last24h.append(df_last24h['close'][index])
        
        # Si on est en version live
        if self.live:
            self.telegram_manager.send_msg("BINANCE LIVE POSITION HAS BEEN CLOSED\n --> Resultat: {0}\n Crypto: {1}".format(self.result, self.crypto_in_position))
        
        # On affiche et on sauvegarde le resultat
        utils.debug(1, '!!! on vend, trade result : {0}'.format(self.result))
        utils.addTestTradeToCsv(self.time, self.crypto_in_position, self.enter_price, self.take_profit, self.stop_loss, self.result, self.candle_length, self.take_profit_ratio, self.stop_loss_ratio, self.day_percent, self.time_in_trade, self.tab_prices, self.last24h, self.tab_times)
        
        # On renitialise les variables pour le prochain trade
        self.restore_variable_for_csv()

    def handle_position(self):
        # On recupere le dernier prix
        close = self.binance_api_manager.get_ws_crypto_price(self.pair)
        if close:
            self.tab_prices.append(close)
            self.tab_times.append(datetime.now().timestamp())
        else:
            close = None

        # Stratégie de sortie    
        if close == None:
            close = None

        # Position gagnante
        elif close >= self.take_profit:
            print(close)
            print(self.binance_api_manager.take_profit)
            self.close_position(result=1)  

        # Position perdante        
        elif close < self.stop_loss:	           
            self.close_position(result=0)

    def take_live_position(self):
        position = self.binance_api_manager

        try:
            utils.debug(2, "TRADING BOT -- TAKE LIVE POSITION - Taking... crypto_found: {0}, self.busd_balance: {1}".format(self.crypto_in_position, self.busd_balance))
            
            # Set le symbole de la crypto
            position.set_symbol(self.crypto_in_position)
            position.set_pair(self.pair)

            # Recupere les resolutions prix et token pour la normalisation des nombres
            position.get_resolutions()
            
            # Recupere le prix de la crypto
            position.set_crypto_price(position.get_ws_crypto_price())

            # Calcule la quantité de token à acheter avec 99% de la self.busd_balance donnée
            position.set_token_quantity(utils.normalizeNumber(position.quantity_resolution, (self.busd_balance*0.99)/position.crypto_price)) 

            # Achete la crypto au prix du marché
            order = position.buy_market()

            if not order:
                raise UnboundLocalError('By market failed')           
            
            # Recupere la quantité de token
            position.set_token_quantity(utils.normalizeNumber(position.quantity_resolution, position.get_token_quantity()))

            # On s'assure que si l'on a acheté la crypto, les ordres de sorties se créaient
            exit_ordered_placed = False
            
            while not exit_ordered_placed:                
                # Calcule les Take profit et Stop loss de la position trouvé
                position.take_profit, position.stop_loss = utils.getTPSLValues(position.crypto_price, self.stop_loss_ratio, self.take_profit_ratio)

                # Place les ordres de sorties (TP, SL et SLL)
                position.set_take_profit(utils.normalizeNumber(position.price_resolution, position.take_profit))
                position.set_stop_loss(utils.normalizeNumber(position.price_resolution, position.stop_loss))
                position.set_stop_loss_limit(position.stop_loss)

                # Créé l'ordre
                exit_ordered_placed = position.create_OCO_order()
                
                # Si l'ordre n'a pas pu être créé, on test la validité de la position avant de réessayer
                if exit_ordered_placed:
                    # Recupere le prix de la crypto
                    position.set_crypto_price(position.get_ws_crypto_price())
                    
                    # Si le prix est en dessous du stop loss d'origine (ou si il a passé le take profit, on sait jamais ...)
                    if position.crypto_price < position.stop_loss or position.crypto_price >= position.take_profit:
                        # Vend l'intégralité des tokens de la crypto au prix du marché
                        exit_ordered_placed = position.sell_market()

            # Modifie les variables TP, SL et enter_price du bot avec les valeurs du live
            self.take_profit = position.take_profit
            self.stop_loss = position.stop_loss
            self.enter_price = position.crypto_price

        except Exception as e:
            utils.debug(2, "TRADING BOT -- ERROR -- TAKE LIVE POSITION - self.busd_balance: {0}, crypto_found: {1}, stopLossRatio: {2}, takeProfitRatio: {3}".format(self.busd_balance, position.symbol, gv.stop_loss_ratio, gv.take_profit_ratio))
            utils.debug(3, str(e))        
            return False
        else:
            utils.debug(1, "TRADING BOT -- TAKE LIVE POSITION - OK crypto_found: {0}, price: {1}, stopLoss: {2}, takeProfit: {3}".format(position.symbol, position.crypto_price, position.stop_loss, position.take_profit))
            self.telegram_manager.send_msg("BINANCE LIVE POSITION HAS BEEN TAKEN\n --> Crypto: {0}\n self.busd_balance: {1} B$\n Nombre de token: {2}\n Price: {3} $\n Take profit: {4} $\n Stop loss: {5}$".format(position.symbol, self.busd_balance, position.token_quantity, self.enter_price, position.take_profit, position.stop_loss))
            utils.saveTrade(datetime.now(), self.busd_balance, position.symbol, position.crypto_price, position.take_profit, position.stop_loss, self.candle_length_limit, self.take_profit_ratio, self.stop_loss_ratio)
            return True

    def open_position(self):
        self.in_position = True
        
        # On recupere le take profit et le stop loss
        self.take_profit, self.stop_loss = utils.getTPSLValues(self.enter_price, self.stop_loss_ratio, self.take_profit_ratio)
        
        # On recupere la data d'entrée en position et la taille de la bougie 1h
        self.time = datetime.now()
        self.candle_length = self.enter_price/self.open
        
        # Si on est en mode LIVE, on rentre REELLEMENT en position
        if self.live and self.busd_balance > 10:
            self.in_position = self.take_live_position()
        
        if self.in_position:
            # On affiche l'entrée en position
            utils.debug(1, "!!!! buy {0} at {1} $ at {2}, take profit at {3} and stop loss at {4}".format(self.crypto_in_position, self.enter_price, self.time, self.take_profit, self.stop_loss))

    def check_entry_conditions(self, index, dfTop):
        pair = dfTop["symbol"][index]
        # si la crypto est sur binance
        if (self.binance_api_manager.is_crypto_tradable(pair)):
            # on recupere la derniere bougie 1h
            dfCandle = pd.DataFrame(self.binance_api_manager.get_candle_stick(pair, Client.KLINE_INTERVAL_1HOUR, '1HOUR'))	                    
            if (not dfCandle.empty):
                open = dfCandle["open"].iloc[-1]
                close = dfCandle["close"].iloc[-1]
                high = dfCandle["high"].iloc[-1]
            else:
                open = 1
                close = 1
                high = 1
            
            utils.debug(4, "TRADING BOT -- CHECK ENTRY CONDITION -- {5} -- open: {0}, close: {1}, high: {2}, bougie1h: {3}, meche: {4}".format(open, close, high, round(close/open, 5), round(high/close, 5), pair))
            
            # STRATEGIE DENTREE	                
            # si la bougie 1h fais minimum 2%
            if (close/open >= float(gv.candle_length_limit)):
                utils.debug(3, "TRADING BOT -- CHECK ENTRY CONDITION -- {5} -- open: {0}, close: {1}, high: {2}, bougie1h: {3}, meche: {4}".format(open, close, high, round(close/open, 5), round(high/close, 5), pair))
                # si elle n'a pas de meche
                if (high/close == 1.0):
                    # On rentre en position
                    self.pair = str(pair)
                    self.crypto_in_position = str(pair).split("BUSD")[0]
                    self.enter_price = close
                    self.open = open
                    self.day_percent = dfTop["priceChangePercent"][index]
                    return True
        
        return False

    def find_a_position(self):
        # On recupere les cryptos gagnantes du jour
        dfTop = pd.DataFrame(self.binance_api_manager.get_daily_winner())
        if (not dfTop.empty):	         	                        
            # Pour chaque crypto
            for index, row in dfTop.iterrows():                
                if self.check_entry_conditions(index, dfTop):
                    utils.debug(2, "TRADING BOT -- FIND A POSITION -- Position found. symbol: {0}, price: {1}".format(self.crypto_in_position, self.enter_price))
                    return True
        
        return False

    def bot_starting(self):
        # Message d'informations 'debut du programme'
        utils.reset_all_logs_file()
        utils.debug(1, "DEBUT DU PROGRAMME (Live: {3}) -- take_profit_ratio : {0}, stop_loss_ratio : {1}, candle_lenght_limite : {2}".format(self.take_profit_ratio, self.stop_loss_ratio, self.candle_length_limit, self.live))

    def bot_stopping(self):
        # Message d'informations 'fin du programme'
        utils.debug(1, "FIN DU PROGRAMME (Live: {3}) -- take_profit_ratio : {0}, stop_loss_ratio : {1}, candle_lenght_limite : {2}".format(self.take_profit_ratio, self.stop_loss_ratio, self.candle_length_limit, self.live))                                                        

    def run(self):
        self.bot_starting()
        while True:
            if self.event:
                if self.event.is_set():
                    break
            if not self.in_position:
                if self.live:
                    self.busd_balance = self.binance_api_manager.get_token_quantity(symbol=gv.trade_currency)
                    if self.busd_balance and self.busd_balance < 10:
                        self.cancel_open_orders()
                if self.find_a_position():
                    self.open_position()
            else:
                self.handle_position()
        self.bot_stopping()