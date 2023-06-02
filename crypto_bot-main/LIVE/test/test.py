from src.lib.binance_api_manager import BinanceApiManager
from src.trading_bot import TradingBot
from binance.client import Client

class Test():
    def __init__(self):
        pass

    def run(self):
        take_profit_ratio = 0.03
        stop_loss_ratio = 0.01
        candle_length_limit = 1.0
        debug = 4

        bot = TradingBot(take_profit_ratio, stop_loss_ratio, candle_length_limit, debug, 0)
        api = BinanceApiManager()

        # SIMPLE BINANCE CLIENT TEST
        # Should be something
        df_candle_stick = api.get_candle_stick("BTCBUSD", Client.KLINE_INTERVAL_1HOUR, '1HOUR')
        print("df_candle_stick: \n{0}".format(df_candle_stick))

        # Should be something
        df_daily_winner = api.get_daily_winner()
        print("df_daily_winner: \n{0}".format(df_daily_winner))

        # Should be True
        bool_is_crypto_tradable = api.is_crypto_tradable("BTCBUSD")
        print("bool_is_crypto_tradable: {0}".format(bool_is_crypto_tradable))

        # Should be something
        float_price_resolution, float_qty_resolution = api.get_resolutions("BTCBUSD")
        print("float_price_resolution: {0}\n float_qty_resolution: {1}".format(float_price_resolution, float_qty_resolution))

        # Should be something
        float_ws_crypto_price = api.get_ws_crypto_price("BTCBUSD")
        print("float_ws_crypto_price: {0}".format(float_ws_crypto_price))

        # Should be something
        float_token_quantity = api.get_token_quantity("BUSD")
        print("float_token_quantity: {0}".format(float_token_quantity))

        # STORY USER CLIENT TEST
        bot.busd_balance = float_token_quantity
        bot.crypto_in_position = "BTC"
        bot.pair = "BTCBUSD"

        # Should buy and place orders on Binance
        bot.take_live_position()

        # Should cancel all open orders and sell on Binance
        bot.cancel_open_orders()