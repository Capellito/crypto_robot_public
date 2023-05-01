import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from binance.client import Client

class DataManager():

    # INIT
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)
        self.api_key = api_key
        self.api_secret = api_secret

        self.starting_date = None

        self.df = None
        self.all_traded_symbols = []
        self.last_orders = []

    # GETTER 
    def get_df_from_csv_source(self, csv_src):
        self.live_df = pd.read_csv(str(csv_src), sep='|')

    def get_all_live_traded_symbols(self):
        self.all_traded_symbols = self.live_df.drop_duplicates("SYMBOL")["SYMBOL"]

    def get_binance_last_orders(self):
        orders_table = []
        for symbol in self.all_traded_symbols:
            last_symbol_orders = self.client.get_all_orders(symbol=symbol+'BUSD')
            for symbol_orders in last_symbol_orders:
                orders_table.append(symbol_orders)
        self.last_orders = orders_table

    def clean_binance_last_orders(self):
        df = pd.DataFrame(self.last_orders)

        df.drop(df[df['status'] != "FILLED"].index, inplace = True)
        # df.drop(df[df['side'] == "SELL"].index, inplace = True)

        df = df.drop(columns=["clientOrderId"])
        df = df.drop(columns=["cummulativeQuoteQty"])
        df = df.drop(columns=["timeInForce"])
        df = df.drop(columns=["icebergQty"])
        df = df.drop(columns=["origQuoteOrderQty"])
        df = df.drop(columns=["isWorking"])
        df = df.drop(columns=["selfTradePreventionMode"])

        df["time"] = df["time"].apply(lambda x: datetime.datetime.fromtimestamp(x / 1000.0))
        df["updateTime"] = df["updateTime"].apply(lambda x: datetime.datetime.fromtimestamp(x / 1000.0))
        df["workingTime"] = df["workingTime"].apply(lambda x: datetime.datetime.fromtimestamp(x / 1000.0))

        df = df.set_index("time")
        df = df.sort_index()

        mask = df.index >= pd.to_datetime(str(self.starting_date))
        df = df[mask]

        self.last_orders = df

    # TODO Generer un data frame des trades réalisé a partir des ordres binance
    def generate_trade_history_data_frame(self):
        pass

    def get_live_data_frame(self):
        pass

    def run(self):
        pass
