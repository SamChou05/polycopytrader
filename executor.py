import os
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.constants import POLYGON
from decimal import Decimal
from config import PRIVATE_KEY, API_KEY, API_SECRET, API_PASSPHRASE, CHAIN_ID, RPC_URL

class Executor:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.client = self._init_client()

    def _init_client(self):
        if not PRIVATE_KEY:
            raise ValueError("PRIVATE_KEY not set in environment")
            
        # Initialize CLOB client
        # Note: In a real scenario, we might need to derive L2 keys if not provided,
        # but for now we assume L2 keys are present or we use L1 for everything if supported.
        # The PRD mentions L2 is standard.
        
        return ClobClient(
            host="https://clob.polymarket.com",
            key=PRIVATE_KEY,
            chain_id=CHAIN_ID,
            signature_type=1, # 1 for private key, 2 for derived
            funder=POLYGON, # Use Polygon network
        )

    def set_api_creds(self, key, secret, passphrase):
        # py-clob-client 0.32.0 might handle this differently.
        # Checking source or docs would be ideal, but based on error:
        # TypeError: ClobClient.set_api_creds() takes 2 positional arguments but 4 were given
        # It likely expects an object or just one argument.
        # However, looking at common usage, it might be create_or_derive_api_creds or similar.
        # Let's try to construct the creds object if needed, or check if we can pass them differently.
        # Actually, the error says "takes 2 positional arguments but 4 were given".
        # self is 1. So it takes 1 other argument. Likely an ApiCreds object.
        from py_clob_client.clob_types import ApiCreds
        creds = ApiCreds(api_key=key, api_secret=secret, api_passphrase=passphrase)
        self.client.set_api_creds(creds)

    def place_order(self, token_id, side, price, size):
        """
        Places an FOK (Fill-Or-Kill) order.
        """
        if self.dry_run:
            print(f"[DRY RUN] Placing order: Token={token_id}, Side={side}, Price={price}, Size={size}")
            return {"orderID": "dry-run-id", "status": "simulated"}

        try:
            order_args = OrderArgs(
                price=price,
                size=size,
                side=side,
                token_id=token_id,
            )
            # Using FOK as per PRD recommendation for copy trading
            resp = self.client.create_and_post_order(order_args, order_type=OrderType.FOK)
            return resp
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

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
