import json
import threading
import websocket

class WebSocketManager:
    
    def __init__(self):
        self.stream_url = None
        self.ws = None
        self.response = None

    def on_message(message):
        print('Received message:', message)

    def on_message(self, ws, message):
        # Traitement des données reçues
        data = json.loads(message)
        self.response = data
        if len(str(data)) > 100:
            self.ws.close()

    def on_error(self, ws, error):
        # Gestion des erreurs
        print(error)

    def on_close(self, ws):
        # Gestion de la fermeture de la connexion
        print("Connexion fermée")

    def on_open(self, ws):
        # Envoi de la demande de données
        self.ws.send(self.stream_url)
    
    def run(self):
        # Etablissement de la connexion WebSocket
        self.ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws",
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever()