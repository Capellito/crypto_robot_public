import PySimpleGUI as sg
import threading
from threading import Event
from src.trading_bot import TradingBot
import src.lib.utils as utils
import path

class TradingAppGUI:
    
    def __init__(self):
        self.thread = None
        self.event = Event()

        # Recuperation de l'output
        with open(path.LOGS, 'r') as f:
            # Lit les 10 dernières lignes du fichier
            self.last_lines = f.readlines()[-1:]

        # Définir la mise en page de l'interface
        self.layout_bot = [
            [sg.T("Trading Bot", font="Default 21", size=(19, 1), justification='c', background_color="#1B2838")],
            [sg.Text("TP:", size=(10, 1)), sg.Push(),
             sg.Slider(key='-TP-', range=(0, 0.05), resolution=0.001, orientation='h', default_value=0.022, size=(20, 15))],
            [sg.Text("SL:", size=(10, 1)), sg.Push(),
             sg.Slider(key='-SL-', range=(0, 0.01), resolution=0.001, orientation='h', default_value=0.008, size=(20, 15))],
            [sg.Text("Bougie 1H:", size=(10, 1)), sg.Push(),
             sg.Slider(key='-CANDLE-', range=(1, 1.2), resolution=0.01, orientation='h', default_value=1.02, size=(20, 15))],
            [sg.Text("Debug:", size=(10, 1)), sg.Push(),
             sg.Slider(key='-DEBUG-', range=(0, 4), resolution=1, orientation='h', default_value=3, size=(20, 15))],
            [sg.Text("")],
            [sg.HSep()],
            [sg.Multiline(default_text=''.join(self.last_lines), size=(43, 4), key='-OUTPUT-', disabled=True, autoscroll=False, no_scrollbar=True, background_color='#2B2B2B', text_color='white')],
            [sg.Combo(['LIVE', 'TEST'], enable_events=True, default_value='TEST', key='-LIVE_OR_TEST-', readonly=True, size=(10, 2)),
             sg.Push(),
             sg.Button('RUN', key="-START_BUTTON-", visible=True, size=(5, 1), button_color=('white', 'green'), border_width=5, font='Any 15'),
             sg.Button('STOP', key="-STOP_BUTTON-", visible=False, size=(5, 1), button_color=('white', 'red'), border_width=5, font='Any 15')]]

        self.layout = self.layout_bot
        
        # Créer une fenêtre avec la mise en page définie
        self.window = sg.Window('Trading Bot GUI', self.layout)

    def stop_thread(self):
        if self.thread:
            self.event.set()
            self.thread.join()
    
    def start_thread(self):
        self.bot = TradingBot(take_profit_ratio=self.tp, stop_loss_ratio=self.sl, candle_length_limit=self.candle, debug=self.debug, live_or_not=self.live_or_test, event=self.event)
        self.event.clear()
        self.thread = threading.Thread(target=self.bot.run)
        self.thread.start()
    
    def swap_button(self, start):        
        self.window['-STOP_BUTTON-'].update(visible=start)
        self.window['-START_BUTTON-'].update(visible=not start)

    def run(self):
        while True:
            event, values = self.window.read(timeout=100)

            # Récupérer les valeurs des champs de saisie
            if event:
                self.debug = values['-DEBUG-']
                self.tp = values['-TP-']
                self.sl = values['-SL-']
                self.candle = values['-CANDLE-']
                if values['-LIVE_OR_TEST-'] == "LIVE":
                    self.live_or_test = 1
                else:
                    self.live_or_test = 0
            if event == sg.WIN_CLOSED:
                self.stop_thread()
                break
            if event == "-STOP_BUTTON-":
                self.stop_thread()
                self.swap_button(start=False)
            if event == '-START_BUTTON-':
                self.start_thread()
                self.swap_button(start=True)
            
            # Ouvre le fichier en mode lecture seule
            with open(path.LOGS, 'r') as f:
                # Lit les 10 dernières lignes du fichier
                self.last_lines = f.readlines()[-1:]
                # self.last_lines.reverse()
                # Afficher les 10 dernières lignes dans le champ de texte
                output = ''.join(self.last_lines)
                self.window['-OUTPUT-'].update(output)
        
        self.window.close()