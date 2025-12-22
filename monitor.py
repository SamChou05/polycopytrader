import json
import threading
import time
import websocket
import requests
from config import RTDS_URL, DATA_API_URL, TARGET_ADDRESS

class Monitor:
    def __init__(self, target_address, callback):
        self.target_address = target_address.lower()
        self.callback = callback # Function to call when trade detected
        self.ws = None
        self.running = False
        self.last_processed_trade_id = None

    def start(self):
        self.running = True
        # Start WebSocket thread
        self.ws_thread = threading.Thread(target=self._run_ws)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # Start Polling thread
        self.poll_thread = threading.Thread(target=self._run_polling)
        self.poll_thread.daemon = True
        self.poll_thread.start()

    def _run_ws(self):
        # RTDS WebSocket connection
        # Note: Subscribing to specific user activity might not be fully supported publicly
        # as per PRD, so we might need to subscribe to 'activity' and filter.
        # For this implementation, we'll try a general subscription and filter client-side.
        
        def on_message(ws, message):
            data = json.loads(message)
            # Parse message and check if it involves target_address
            # This is a simplified handler. Real RTDS messages need specific parsing.
            # Assuming 'orders_matched' event structure.
            if isinstance(data, list):
                for event in data:
                    self._process_event(event)
            else:
                self._process_event(data)

        def on_error(ws, error):
            print(f"WS Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            print("WS Closed")
            if self.running:
                time.sleep(5)
                self._run_ws() # Reconnect

        def on_open(ws):
            print("WS Opened")
            # Subscribe command
            sub_msg = {
                "type": "subscribe",
                "channel": "activity", # Hypothetical channel
                "params": {}
            }
            ws.send(json.dumps(sub_msg))

        # websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(RTDS_URL,
                                         on_open=on_open,
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close)
        self.ws.run_forever()

    def _run_polling(self):
        while self.running:
            try:
                self._poll_data_api()
            except Exception as e:
                print(f"Polling error: {e}")
            time.sleep(5) # Poll every 5 seconds

    def _poll_data_api(self):
        url = f"{DATA_API_URL}/activity"
        params = {"user": self.target_address, "limit": 10}
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            activities = resp.json()
            for activity in activities:
                # Check if new
                # Need a mechanism to deduplicate with WS events
                self._process_event(activity, source="polling")

    def _process_event(self, event, source="ws"):
        # Logic to extract trade details: side, size, price, asset
        # and call self.callback(trade_details)
        # Filter by self.target_address
        
        # Placeholder logic
        maker = event.get('maker', '').lower()
        taker = event.get('taker', '').lower()
        
        if self.target_address in [maker, taker]:
            print(f"Trade detected via {source}: {event}")
            # Construct trade object
            trade = {
                'asset': event.get('asset'),
                'side': 'BUY' if self.target_address == taker else 'SELL', # Simplified
                'size': event.get('size'),
                'price': event.get('price'),
                'timestamp': event.get('timestamp')
            }
            self.callback(trade)

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
