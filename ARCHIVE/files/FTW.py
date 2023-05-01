### VERSION 1.1
### Strategie : On cherche a rentrer sur une crypto gagnante de binance qui est en pleine montee. 
###                    Si une crypto gagnante a sa bougie 1h verte et quelle est en train de grandir (pas de meche haute) alors on rentre en se disant quon a peu de chance que ce soit le top.

##### IMPORT #####
from datetime import datetime, timedelta
from binance.client import Client

import pandas as pd
import sys

##### FUNCTION #####

###
# FUNCTION IS CRYPTO TRADABLE
# PARAM : crypto symbol
# --> retourne TRUE si la crypto est disponible sur binance
def isCryptoTradable(cryptoSymbol):
    try:
        df = Client().get_symbol_info(symbol=cryptoSymbol)
    except:
        print('sans doute times out is crypto tradable')
    else:
               if (df == None):
                   return False
               if (df['status'] == "TRADING"):
                   return True
        
    return False
###

###
# FUNCTION GET DAILY WINNER
# PARAM : none
# --> retourne les cryptos gagnantes du jour (only USDT pair)
def getDailyWinner():
    try:
        # on recupere toute les crypto et info des 24h
        tickers = Client().get_ticker()
    except:
       print('sans doute time out getDailyWinner')
       df = pd.DataFrame()
    else:
           df = pd.DataFrame(tickers)
           
           df["priceChangePercent"] = pd.to_numeric( df["priceChangePercent"])
           
           # on ne veut que les pair BUSD
           df['indice'] = df['symbol'].str.split('BUSD').str[1]
           df = df[df['indice']=='']
           
           # On trie par winner
           df = df.sort_values(by=["priceChangePercent"], ascending=False)
           
           del df['priceChange']
           df.drop(df[df["priceChangePercent"] <= 8].index, inplace = True)
        
    return df
###

###
# FUNCTION GET CANDLE STICK
# PARAM : crypto symbol | interval | duration
# --> retourne les bougies demande de la crypto sur la duree donnee
def getCandleStick(cryptoSymbol, interval, duration):
    try:
        klinesT = Client().get_historical_klines(cryptoSymbol, interval, duration)		    
    except:
        print('timed out get candle stick')
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
###

###
# FUNCTION ADD TRADE TO CSV
# PARAM : TIME | SYMBOL | ENTER_PRICE | TAKE_PROFIT | STOP_LOSS | RESULT | CANDLE_LENGTH | TP_RATIO | SL_RATIO | DAY_PERCENT | TIME_IN_TRADE | ATH | ATL | TAB_PRICES | LAST_24H | TAB_TIMES
# --> ajoute un trade finit a l'historique' des trades
def addTradeToCsv(time, symbol, enterPrice, TP, SL, result, candleLength, TPRatio, SLRatio, dayPercent, timeInTrade, ATH, ATL, tabPrices, last24h, tabTimes):
    with open('BACKTEST/trade_history/trade_history.csv', 'a') as f:
        f.write('\n{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}|{9}|{10}|{11}|{12}|{13}|{14}|{15}'.format(time, symbol, enterPrice, TP, SL, result, candleLength, TPRatio, SLRatio, dayPercent, timeInTrade, ATH, ATL, tabPrices, last24h, tabTimes))
###

##### MAIN #####

# constante
# TO START : python FTW.py 0.03 0.02 1.02 1
takeProfitRatio = float(sys.argv[1])
stopLossRatio = float(sys.argv[2])
candleLengthLimit = float(sys.argv[3])
debug = 0
# variable globale
inPosition = False
cryptoInPosition =''
takeProfit = 0
stopLoss = 0

# print
print("debut du programme", datetime.now())
print("takeProfitRatio : {0}, stopLossRatio : {1}, candleLengthLimite : {2}".format(takeProfitRatio, stopLossRatio, candleLengthLimit))

# trade history variable
time = None
enterPrice = None
TP = None
SL = None
result = None
candleLength = None
dayPercent = None
timeInTrade = None
ATH = None
ATL = None
tabPrices = []
tabTimes = []
last24h = []    	

while(1):
    # POSITION ON
    if inPosition:
        # On recupere les dernieres bougies
        lastCandle = pd.DataFrame(getCandleStick(cryptoInPosition, Client.KLINE_INTERVAL_1MINUTE, '2MINUTE'))
        if (not lastCandle.empty):
            close = lastCandle["close"].iloc[-1]
            tabPrices.append(close)
            tabTimes.append(datetime.now().timestamp())
        else:
            close = None
         
        # on calcule l'ATH et ATR du trade courant
        if ATH == None:
            ATH = close
            ATL = close
        elif close == None:
            close = None
        elif close > ATH:
            ATH = close
        elif close < ATL:
            ATL = close
            
        # STRATEGIE DE SORTIE    
        if close == None:
            close = None
        # GAGNANTE
        elif close >= takeProfit:
               # print
               print('on vend a {0} a {1}, trade GAGNANT'.format(takeProfit, datetime.now()))
               # csv
               result = 1
               timeInTrade = time - (datetime.now())
               dfLast24h = getCandleStick(cryptoInPosition, Client.KLINE_INTERVAL_1HOUR, '24HOUR')
               if not dfLast24h.empty:
                   for index, row in dfLast24h.iterrows():
                       last24h.append(dfLast24h['close'][index])
                                           
               addTradeToCsv(time, cryptoInPosition, enterPrice, TP, SL, result, candleLength, takeProfitRatio, stopLossRatio, dayPercent, timeInTrade, ATH, ATL, tabPrices, last24h, tabTimes)
               
               # On renitialise pour le prochan trade
               inPosition = False
               cryptoInPosition =''
               takeProfit = 0
               stopLoss = 0
               ATH = None
               ATL = None
               tabPrices = []
               tabTimes = []
               last24h = []
                          
       # PERDANTE        
        elif close <= stopLoss:	           
               # print
               print('on vend a {0} a {1}, trade PERDANT'.format(stopLoss, datetime.now()))
               # csv
               result = 0
               timeInTrade = time - (datetime.now())
               dfLast24h = getCandleStick(cryptoInPosition, Client.KLINE_INTERVAL_1HOUR, '24HOUR')
               if not dfLast24h.empty:
                   for index, row in dfLast24h.iterrows():
                       last24h.append(dfLast24h['close'][index])
                                  
               addTradeToCsv(time, cryptoInPosition, enterPrice, TP, SL, result, candleLength, takeProfitRatio, stopLossRatio, dayPercent, timeInTrade, ATH, ATL, tabPrices, last24h, tabTimes)
               
               # On renitialise pour le prochain trade	           	           	           	           
               inPosition = False
               cryptoInPosition =''
               takeProfit = 0
               stopLoss = 0
               ATH = None
               ATL = None
               tabPrices = []
               tabTimes = []
               last24h = []	           
                                             
     # POSITION OFF                  
    else:
        # On recupere les cryptos gagnantes du jour
        dfTop = pd.DataFrame(getDailyWinner())
        if (not dfTop.empty):	         	                        
            if (debug):
                print(dfTop)
            # Pour chaque crypto
            for index, row in dfTop.iterrows():
                symbol = dfTop["symbol"][index]
                # si la crypto est sur binance
                if (isCryptoTradable(symbol)):
                        # on recupere la derniere bougie
                        dfCandle = pd.DataFrame(getCandleStick(symbol, Client.KLINE_INTERVAL_1HOUR, '1HOUR'))	                    
                        if (not dfCandle.empty):
                            openc = dfCandle["open"].iloc[-1]
                            close = dfCandle["close"].iloc[-1]
                            high = dfCandle["high"].iloc[-1]
                        else:
                            openc =1
                            close = 1
                            high = 1
                        # STRATEGIE DENTREE	                
                        # si la bougie 1h fais minimum 2%
                        if (close/openc >= float(candleLengthLimit)):
                            # si elle n'a pas de meche
                            if (high/close == 1.0):
                                # On rentre en position
                                inPosition = True
                                cryptoInPosition = symbol
                                takeProfit = close + close*takeProfitRatio
                                stopLoss = close - close*stopLossRatio
                                                                
                                # print
                                print("!!!! buy {0} at {1} $ at {2}, take profit at {3} and stop loss at {4}".format(symbol, close, datetime.now(), takeProfit, stopLoss))
                                # csv
                                time = datetime.now()
                                TP = takeProfit
                                SL = stopLoss
                                enterPrice = close
                                candleLength = close/openc
                                dayPercent = dfTop["priceChangePercent"][index]
                                                                                               
                                break	                    
                        
                        if (debug):
                            print(dfCandle['timestamp'].iloc[-1])
                            print("open : {0}, close : {1}, high : {2} \n close/open : {3}, high/close : {4}".format(openc, close, high, close/openc, high/close))	  
                            
