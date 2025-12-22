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
        # Correct Polymarket RTDS WebSocket URL
        rtds_url = "wss://ws-live-data.polymarket.com"
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                # RTDS message structure: { topic, type, timestamp, payload }
                # We are interested in 'activity' topic with 'orders_matched' type
                topic = data.get('topic')
                msg_type = data.get('type')
                payload = data.get('payload', {})
                
                if topic == 'activity' and msg_type == 'orders_matched':
                    self._process_event(payload)
                elif isinstance(data, list):
                    for event in data:
                        self._process_event(event)
            except json.JSONDecodeError:
                pass # Ignore non-JSON messages (like PONG)

        def on_error(ws, error):
            print(f"WS Error: {error}")

        def on_close(ws, close_status_code, close_msg):
            print("WS Closed")
            if self.running:
                time.sleep(5)
                self._run_ws() # Reconnect

        def on_open(ws):
            print("WS Opened")
            # Correct subscription format per Polymarket docs
            sub_msg = {
                "action": "subscribe",
                "subscriptions": [
                    {
                        "topic": "activity",
                        "type": "orders_matched",
                        # Optional: For user-specific activity, use gamma_auth
                        "gamma_auth": {
                            "address": self.target_address
                        }
                    }
                ]
            }
            ws.send(json.dumps(sub_msg))
            
            # Start heartbeat thread
            def send_ping():
                while self.running and ws.sock and ws.sock.connected:
                    try:
                        ws.send("PING")
                    except Exception:
                        break
                    time.sleep(5)
            
            ping_thread = threading.Thread(target=send_ping)
            ping_thread.daemon = True
            ping_thread.start()

        self.ws = websocket.WebSocketApp(rtds_url,
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
            # Calculate latency
            event_timestamp = event.get('timestamp')
            now_ms = int(time.time() * 1000)
            
            if event_timestamp:
                # Handle both seconds and milliseconds timestamps
                if event_timestamp < 10000000000:  # Seconds
                    event_timestamp_ms = event_timestamp * 1000
                else:  # Already milliseconds
                    event_timestamp_ms = event_timestamp
                    
                latency_ms = now_ms - event_timestamp_ms
                print(f"⚡ Trade detected via {source} | Latency: {latency_ms}ms")
            else:
                print(f"Trade detected via {source}: (no timestamp)")
            
            # Construct trade object
            trade = {
                'asset': event.get('asset'),
                'side': 'BUY' if self.target_address == taker else 'SELL', # Simplified
                'size': event.get('size'),
                'price': event.get('price'),
                'timestamp': event.get('timestamp'),
                'latency_ms': latency_ms if event_timestamp else None
            }
            self.callback(trade)

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
