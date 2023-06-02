import src.global_variables as global_variables
import path
from datetime import datetime

def log(msg):
    with open(path.LOGS, 'a') as f:
        f.write("\n {0}".format(msg))

def all_logs(msg):
    with open(path.ALL_LOGS, 'a') as f:
        f.write("\n {0}".format(msg))

def reset_all_logs_file():
    with open(path.ALL_LOGS, 'w') as f:
        f.write(' ')

def debug(level, msg):
    msg = str(datetime.now()) + " --- " + str(msg)
    if level <= global_variables.debug:
        print(msg)
        log(msg)
    all_logs(msg)

def normalizeNumber(resolution, number):
    if resolution >= 1:
        number = number-(number%resolution)
    else:
        number = number-(number%resolution)
        number = float(str(number)[:8])

    return number

def saveTrade(date, busd_balance, symbol, enter_price, take_profit, stop_loss, candle_length, take_profit_ratio, stop_loss_ratio):
    with open(path.LIVE_HISTORY, 'a') as f:
        f.write('\n{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}'.format(date, busd_balance, symbol, enter_price, take_profit, stop_loss, candle_length, take_profit_ratio, stop_loss_ratio))

def addTestTradeToCsv(time, symbol, enterPrice, TP, SL, result, candleLength, TPRatio, SLRatio, dayPercent, timeInTrade, tabPrices, last24h, tabTimes):
    with open(path.TRADE_HISTORY, 'a') as f:
        f.write('\n{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}|{9}|{10}|{11}|{12}|{13}'.format(time, symbol, enterPrice, TP, SL, result, candleLength, TPRatio, SLRatio, dayPercent, timeInTrade, tabPrices, last24h, tabTimes))

def getTPSLValues(price, stopLossRatio, takeProfitRatio):
    takeProfit = price + price*takeProfitRatio
    stopLoss = price - price*stopLossRatio    

    debug(3, "BINANCE LIVE FUNCTIONS -- GET TP & SL -- TP: {0}, SL: {1}".format(takeProfit, stopLoss))

    return takeProfit, stopLoss