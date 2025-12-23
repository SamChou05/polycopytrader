import os
import logging
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, ApiCreds
from decimal import Decimal
from config import PRIVATE_KEY, API_KEY, API_SECRET, API_PASSPHRASE, CHAIN_ID, RPC_URL

class Executor:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.client = None
        self._creds_set = False

    def _init_client(self, api_key=None, api_secret=None, api_passphrase=None):
        if not PRIVATE_KEY:
            raise ValueError("PRIVATE_KEY not set in environment")
        
        # Create credentials object if provided
        creds = None
        if api_key and api_secret and api_passphrase:
            creds = ApiCreds(api_key=api_key, api_secret=api_secret, api_passphrase=api_passphrase)
            logging.info("Initializing CLOB client with API credentials")
        else:
            logging.info("Initializing CLOB client without credentials (read-only)")
            
        # Initialize CLOB client with credentials at init time
        client = ClobClient(
            host="https://clob.polymarket.com",
            chain_id=137,  # Polygon Mainnet
            key=PRIVATE_KEY,
            creds=creds,
            signature_type=0,  # EOA wallet
        )
        
        return client

    def set_api_creds(self, key, secret, passphrase):
        """Initialize client with API credentials for authenticated trading."""
        self.client = self._init_client(key, secret, passphrase)
        self._creds_set = True

    def place_order(self, token_id, side, price, size):
        """
        Places a limit order on Polymarket.
        Returns dict with success status and details.
        """
        if self.dry_run:
            logging.info(f"[DRY RUN] Would place {side} order: {size:.4f} shares @ ${price:.2f}")
            return {"success": True, "orderID": "dry-run-id", "status": "simulated"}
        
        if self.client is None:
            logging.warning("Client not initialized, initializing now...")
            self.client = self._init_client()

        try:
            logging.info(f"Creating order: {side} {size:.4f} @ ${price:.2f} for token {token_id[:20]}...")
            
            order_args = OrderArgs(
                price=price,
                size=size,
                side=side,
                token_id=token_id,
            )
            
            resp = self.client.create_and_post_order(order_args)
            
            if resp:
                logging.info(f"Order placed successfully: {resp}")
                return {"success": True, "response": resp}
            else:
                logging.warning("Order returned empty response")
                return {"success": False, "error": "No response from server"}
                
        except Exception as e:
            error_str = str(e)
            
            # Detect Cloudflare blocks
            if "403" in error_str and ("cloudflare" in error_str.lower() or "blocked" in error_str.lower()):
                logging.error("⛔ Cloudflare is blocking this IP. Try a different VPN server.")
                return {"success": False, "error": "Cloudflare block - try different VPN server"}
            
            # Log and return other errors
            logging.error(f"Order failed: {error_str[:200]}")
            return {"success": False, "error": error_str[:500]}

    def get_market_price(self, token_id):
        # Helper to get current mid-price or best ask/bid
        try:
            ob = self.client.get_order_book(token_id)
            if ob.bids and ob.asks:
                best_bid = float(ob.bids[0].price)
                best_ask = float(ob.asks[0].price)
                return (best_bid + best_ask) / 2.0
            return None
        except Exception:
            return None
