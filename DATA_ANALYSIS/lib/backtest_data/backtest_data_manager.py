import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from binance.client import Client
import lib.backtest_data.backtest_data_services as services

class BacktestDataManager():

    # INIT
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)
        self.api_key = api_key
        self.api_secret = api_secret

        self.winner_fees = 0.001
        self.looser_fees = 0.0015

        self.starting_date = None

        self.df = None
        self.best_parameter_data_frame = None
        self.ratio_1h_24h_candles_data_frame = None

    # GETTER
    def get_df_from_csv_source(self, csv_src):
        self.df = pd.read_csv(str(csv_src), sep='|')

    def clean_dataset(self):
        # clean dataset
        self.df = self.df.dropna()
        self.df = self.df.drop_duplicates()
        self.df['TIME'] = pd.to_datetime(self.df['TIME'])
        self.df['CANDLE_LENGTH'] = (pd.to_numeric(self.df['CANDLE_LENGTH'])-1)*100
        self.df['RESULT'] = pd.to_numeric(self.df['RESULT'])
        self.df['CANDLE_RATIO'] = self.df['DAY_PERCENT']/self.df['CANDLE_LENGTH']
        self.df['ENTER_PRICE'] = pd.to_numeric(self.df['ENTER_PRICE'])
        self.df['TP_RATIO'] = pd.to_numeric(self.df['TP_RATIO'])
        self.df['SL_RATIO'] = pd.to_numeric(self.df['SL_RATIO'])
        self.df['TIME_IN_TRADE'] = self.df['TIME_IN_TRADE'].apply(lambda x: services.date_to_seconds(x))
        self.df['wallet_state'] = 0
        self.df['actual_draw_back'] = 0
        self.df = self.df.set_index("TIME")
        self.df = self.df.sort_index()

    def get_data_set_from_date(self, date):
        mask = self.df.index >= pd.to_datetime(date)
        self.df = self.df[mask]

    def get_data_set_from_ratios(self, tp_ratio, sl_ratio):
        self.df = self.df[(self.df['TP_RATIO']==tp_ratio) & (self.df['SL_RATIO']==sl_ratio)]

    def calculate_best_parameters(self, bougie1hRangeStart, bougie1hRangeStop, TPRatioRangeStart, TPRatioRangeStop , SLRatioRangeStart, SLRatioRangeStop):
        df = self.df

        dfResult = pd.DataFrame(columns = ['1H', '24H', 'SL', 'TP', 'USDT', 'OK', 'NOK'])

        # pour chaque bougie 1h
        for bougie1h in range(bougie1hRangeStart, bougie1hRangeStop, 2):
            # pour chaque bougie 24h
            for bougie24h in range(8, 9, 1):
                # pour chaque stop loss
                for i in range(SLRatioRangeStart, SLRatioRangeStop, 1):    
                    SLRatio = i*0.001
                    # pour chaque take profit
                    for j in range(TPRatioRangeStart, TPRatioRangeStop, 1):
                        TPRatio = j*0.001
                        ok = 0
                        nok = 0
                        usdt = 1000
                        # pour chaque trade
                        for index, row in df.iterrows():
                                # On test le nouveau parametre bougie 1h (CANDLE LENGTH dans le csv)
                                if row["CANDLE_LENGTH"] >= bougie1h:
                                    # On test le nouveau parametre bougie 1h (DAY PERCENT dans le csv)
                                    if row["DAY_PERCENT"] >= bougie24h:
                                        # On test les nouveaux ratio de TP et SL                  
                                        if services.checkOtherRatios(row['ENTER_PRICE'], services.getDfFromString(row['TAB_PRICES']), SLRatio, TPRatio):
                                            ok += 1
                                            usdt = usdt+usdt*TPRatio
                                            usdt = usdt-usdt*self.winner_fees                
                                        else:
                                            nok += 1
                                            usdt = usdt-usdt*SLRatio
                                            usdt = usdt-usdt*self.looser_fees
                                            
                        dfResult = dfResult.append({'1H': bougie1h, '24H': bougie24h, 'SL': SLRatio, 'TP': TPRatio, 'USDT': usdt, 'OK': ok, 'NOK': nok}, ignore_index=True)
        
        dfResult["RATIO"] = dfResult["OK"]/(dfResult["OK"]+dfResult["NOK"])
        dfResult["NB"] = dfResult["OK"]+dfResult["NOK"]

        self.best_parameter_data_frame = dfResult
    
    def calculate_1h_24h_candles_ratio(self, candleLenghtRange, SLRatio, TPRatio):
        # TEST DES LONGUEURS DE BOUGIE 1H (de 1.02 a 1.07)
        dfLengthResult = pd.DataFrame(columns = ["CANDLE_LENGTH", 'OK', 'NOK', 'RATIO'])

        # pour chaque longueur de bougie
        for i in range(1, candleLenghtRange, 1): 
            candleLength = i
            lengthOK = 0
            lengthNOK = 0
            lengthRatio = 0
            
            # pour chaque trade
            for index, row in self.df.iterrows():
                # On test la valeur du day percent afin de pouvoir comparé la combinaisaon daypercent / bougie 1h
                if (row["DAY_PERCENT"] >= 8):
                    # si la longueur de bougie est comprise dans la section testé
                    if (row["CANDLE_LENGTH"] >= candleLength):
                        # On vérifie le resultat du trade en fonction des parametre SLRatio et TPRatio
                        if services.checkOtherRatios(row['ENTER_PRICE'], services.getDfFromString(row['TAB_PRICES']), SLRatio, TPRatio):
                            lengthOK += 1
                        else:
                            lengthNOK += 1
            if lengthNOK == 0:
                lengthNOK += 1             
            lengthRatio = lengthOK/(lengthNOK+lengthOK)

            # on sauvegarde tout les resultats
            d = {"CANDLE_LENGTH": [candleLength], 'OK': [lengthOK], 'NOK': [lengthNOK], 'RATIO': [lengthRatio]}
            dfToAppend = pd.DataFrame(data=d)
            dfLengthResult = pd.concat((dfLengthResult, dfToAppend), axis=0)

            self.ratio_1h_24h_candles_data_frame = dfLengthResult

    def calculate_wallet_state(self, usdt, simpleTPRatio, simpleSLRatio, simpleBougie1h, simpleBougie24h):
        maxUsdt = 0
        drawback = 0

        tt = self.df

        for index, row in tt.iterrows():
            result = "nope"
            # On test le nouveau parametre bougie 1h (CANDLE LENGTH dans le csv)
            if row["CANDLE_LENGTH"] >= simpleBougie1h:
                # On test le nouveau parametre bougie 1h (DAY PERCENT dans le csv)
                if row["DAY_PERCENT"] >= simpleBougie24h:
                    result = services.checkOtherRatios(row['ENTER_PRICE'], services.getDfFromString(row['TAB_PRICES']), simpleSLRatio, simpleTPRatio)
                    if result == True:
                        usdt = usdt+usdt*simpleTPRatio
                        usdt = usdt-usdt*self.winner_fees                
                    elif result == False:
                        usdt = usdt-usdt*simpleSLRatio
                        usdt = usdt-usdt*self.looser_fees
                    
                    # Detection du drawback
                    if usdt > maxUsdt:
                        maxUsdt = usdt
                    drawback = maxUsdt / usdt

            tt["wallet_state"][index] = usdt
            tt["actual_draw_back"][index] = drawback
            if result == "nope":
                tt["RESULT"] = "nope"
            else:
                tt["RESULT"] = result

    # PLOTS
    def plot_ratio_1h_24h_candles(self):
        plt.plot(self.ratio_1h_24h_candles_data_frame['CANDLE_LENGTH'], self.ratio_1h_24h_candles_data_frame['RATIO'])
        plt.ylabel("ratio ok/nok")
        plt.xlabel("candle length 1h")
        plt.show()

    def plot_wallet_state(self):
        # creation du graphique
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(self.df.index, self.df["wallet_state"])   
        # ajout de légendes et de titres
        ax.set_xlabel('trades')
        ax.set_ylabel('USDT')
        ax.set_title('Etat du portefeuille')    
        # affichage du graphique
        plt.show()

    def plot_best_parameters(self):
        df = self.best_parameter_data_frame
        # création du graphique
        fig = plt.figure()
        fig.set_figheight(10)
        fig.set_figwidth(10)

        ax = fig.add_subplot(111, projection='3d')
        sc = ax.scatter(df['1H'], df['SL'], df['TP'], c=df['USDT'], cmap='rainbow', marker='o', s=50)

        # ajout de légendes et de titres
        ax.set_xlabel('1H')
        ax.set_ylabel('SL')
        ax.set_zlabel('TP')
        ax.set_title('MEILLEUR PARAMETRE BOUGIE 1H, SL ET TP')

        # ajout de la barre de couleur
        fig.colorbar(sc)

        # affichage du graphique
        plt.show()

    def plot_best_parameter_for_1h_candle(self, candle_1h):
        # création du graphique
        dfPlotTpSl = self.best_parameter_data_frame[self.best_parameter_data_frame["1H"] == candle_1h]
        dfPlotTpSl.plot.scatter(x='SL', y='TP', c='USDT', colormap='rainbow')
        plt.show()
    
    def run(self):
        pass
