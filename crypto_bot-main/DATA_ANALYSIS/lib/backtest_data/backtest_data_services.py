import pandas as pd

## convertis la données TIME_IN_TRADE du csv en secondes
def date_to_seconds(date):
    base = pd.to_datetime("00:00:00.000000")
    time = pd.to_datetime(str(date).split(", ")[1])
    diff = pd.to_datetime(str(base-time).split("days +")[1])
    diff = pd.to_datetime(str(diff).split(" ")[1])

    return (diff.hour*3600 + diff.minute*60 + diff.second)

## retourne un dataframe a partir dun string
def getDfFromString(str):
    str = str.replace(' ', '')
    str = str[1:-1]
    tab = str.split(',')
    df = pd.DataFrame(tab, columns = ['PRICE'])
    df.drop(df[df['PRICE'] == 'None'].index, inplace = True)
    df['PRICE'] = pd.to_numeric(df['PRICE'])
   
    return df

## retourne le prix de sortie du trade en entrée
def getPriceWithOtherRatio(enterPrice, candles, SLRatio, TPRatio):
    SL = enterPrice - enterPrice*SLRatio
    TP = enterPrice + enterPrice*TPRatio
    for index, row in candles.iterrows():
              if (row['PRICE'] <= SL):
                  return SL            
              elif (row['PRICE'] >= TP):
                  return TP                  
    return None

## retourne true si le trade aurait fonctionner avec un autre stop loss et un autre take profit avec la stratégie de base
def checkOtherRatios(enterPrice, candles, SLRatio, TPRatio):
    SL = float(enterPrice - enterPrice*SLRatio)
    TP = float(enterPrice + enterPrice*TPRatio)
    for index, row in candles.iterrows():
        price = float(candles["PRICE"][index])
        if (price < SL):
            return False            
        elif (price >= TP):
            return True
    return "nope"