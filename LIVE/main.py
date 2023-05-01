### VERSION GUI LIVE 2.0
### Strategie : On cherche a rentrer sur une crypto gagnante de binance qui est en pleine montee. 
### Si une crypto gagnante a sa bougie 1h en pleine croissance (bougie verte et pas de meche haute), 
### alors on rentre en se disant quon a peu de chance que ce soit le top.
### 

from src.trading_app_gui import TradingAppGUI

def main():
    # Créer une instance de la classe StrategyGUI
    gui = TradingAppGUI()

    # Lancer l'interface graphique
    gui.run()

if __name__ == '__main__':
    main()