"""
Trade Monitor for Polymarket Copy Trader.
Monitors multiple wallet addresses via WebSocket and REST polling.
"""

import json
import threading
import time
from typing import Callable, List, Set, Optional, Dict, Any

import websocket
import requests

from config import RTDS_URL, DATA_API_URL
from logger import get_monitor_logger
from exceptions import WebSocketConnectionError, APIRateLimitError

logger = get_monitor_logger()


class Monitor:
    """
    Monitors Polymarket for trades from target wallet addresses.
    Uses both WebSocket (real-time) and REST polling (fallback).
    """
    
    def __init__(
        self, 
        target_addresses: List[str] | str, 
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Initialize the monitor.
        
        Args:
            target_addresses: Single address or list of addresses to monitor
            callback: Function to call when a trade is detected
        """
        # Normalize to list of lowercase addresses
        if isinstance(target_addresses, str):
            target_addresses = [target_addresses]
        self.target_addresses: Set[str] = {addr.lower() for addr in target_addresses}
        
        self.callback = callback
        self.ws: Optional[websocket.WebSocketApp] = None
        self.running = False
        self.processed_trades: Set[str] = set()  # For deduplication
        
        logger.info(f"Monitor initialized for {len(self.target_addresses)} address(es)")
    
    def add_address(self, address: str) -> None:
        """Add an address to monitor."""
        self.target_addresses.add(address.lower())
        logger.info(f"Added address to monitor: {address[:10]}...")
    
    def remove_address(self, address: str) -> None:
        """Remove an address from monitoring."""
        self.target_addresses.discard(address.lower())
        logger.info(f"Removed address from monitor: {address[:10]}...")
    
    def start(self) -> None:
        """Start the monitoring threads."""
        self.running = True
        
        # Start WebSocket thread
        self.ws_thread = threading.Thread(target=self._run_ws, name="monitor-ws")
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # Start Polling thread
        self.poll_thread = threading.Thread(target=self._run_polling, name="monitor-poll")
        self.poll_thread.daemon = True
        self.poll_thread.start()
        
        logger.info("Monitor started")
    
    def stop(self) -> None:
        """Stop the monitoring threads."""
        self.running = False
        if self.ws:
            self.ws.close()
        logger.info("Monitor stopped")
    
    def _run_ws(self) -> None:
        """WebSocket connection loop with auto-reconnect."""
        
        def on_message(ws, message: str) -> None:
            try:
                data = json.loads(message)
                topic = data.get('topic')
                msg_type = data.get('type')
                payload = data.get('payload', {})
                
                if topic == 'activity' and msg_type == 'orders_matched':
                    self._process_event(payload, source="ws")
                elif isinstance(data, list):
                    for event in data:
                        self._process_event(event, source="ws")
            except json.JSONDecodeError:
                pass  # Ignore non-JSON messages (like PONG)
            except Exception as e:
                logger.error(f"Error processing WS message: {e}")
        
        def on_error(ws, error) -> None:
            logger.warning(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg) -> None:
            logger.info(f"WebSocket closed: {close_msg or 'unknown reason'}")
            if self.running:
                time.sleep(5)
                self._run_ws()  # Reconnect
        
        def on_open(ws) -> None:
            logger.info("WebSocket connected")
            
            # Subscribe to activity for each address
            for address in self.target_addresses:
                sub_msg = {
                    "action": "subscribe",
                    "subscriptions": [
                        {
                            "topic": "activity",
                            "type": "orders_matched",
                            "gamma_auth": {"address": address}
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
            
            ping_thread = threading.Thread(target=send_ping, name="ws-ping")
            ping_thread.daemon = True
            ping_thread.start()
        
        try:
            self.ws = websocket.WebSocketApp(
                RTDS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise WebSocketConnectionError(str(e))
    
    def _run_polling(self) -> None:
        """REST API polling loop."""
        while self.running:
            for address in list(self.target_addresses):
                try:
                    self._poll_address(address)
                except Exception as e:
                    logger.warning(f"Polling error for {address[:10]}...: {e}")
            time.sleep(5)  # Poll every 5 seconds
    
    def _poll_address(self, address: str) -> None:
        """Poll the Data API for a specific address."""
        url = f"{DATA_API_URL}/activity"
        params = {"user": address, "limit": 10}
        
        resp = requests.get(url, params=params, timeout=10)
        
        if resp.status_code == 429:
            raise APIRateLimitError("Rate limit exceeded")
        
        if resp.status_code == 200:
            activities = resp.json()
            for activity in activities:
                # Deduplicate using transaction hash
                tx_hash = activity.get('transactionHash')
                if tx_hash and tx_hash in self.processed_trades:
                    continue
                if tx_hash:
                    self.processed_trades.add(tx_hash)
                    # Limit size of processed trades set
                    if len(self.processed_trades) > 1000:
                        self.processed_trades = set(list(self.processed_trades)[-500:])
                self._process_event(activity, source="polling")
    
    def _process_event(self, event: Dict[str, Any], source: str = "ws") -> None:
        """
        Process a trade event and call callback if it matches a target.
        
        Args:
            event: Raw event data from API
            source: Where the event came from ("ws" or "polling")
        """
        # Extract addresses from event
        proxy_wallet = event.get('proxyWallet', '').lower()
        maker = event.get('maker', '').lower()
        taker = event.get('taker', '').lower()
        
        # Check if any target is involved
        involved_address = None
        for addr in [proxy_wallet, maker, taker]:
            if addr and addr in self.target_addresses:
                involved_address = addr
                break
        
        if not involved_address:
            return
        
        # Calculate latency
        event_timestamp = event.get('timestamp')
        now_ms = int(time.time() * 1000)
        latency_ms = None
        
        if event_timestamp:
            if event_timestamp < 10000000000:  # Seconds
                event_timestamp_ms = event_timestamp * 1000
            else:  # Already milliseconds
                event_timestamp_ms = event_timestamp
            latency_ms = now_ms - event_timestamp_ms
        
        # Determine side
        side = event.get('side', 'BUY')
        if not side and involved_address == taker:
            side = 'BUY'
        elif not side:
            side = 'SELL'
        
        # Build trade object
        trade = {
            'wallet_address': involved_address,
            'asset': event.get('asset'),
            'side': side,
            'size': event.get('size'),
            'price': event.get('price'),
            'timestamp': event.get('timestamp'),
            'latency_ms': latency_ms,
            'title': event.get('title', 'Unknown'),
            'outcome': event.get('outcome', 'Unknown'),
            'source': source,
        }
        
        # Log detection
        logger.info(
            f"Trade detected via {source} | "
            f"{trade['title'][:20]} - {trade['outcome']}: "
            f"{trade['side']} {trade['size']} @ ${trade['price']} | "
            f"Latency: {latency_ms}ms"
        )
        
        # Call callback
        self.callback(trade)

