import os
from dotenv import load_dotenv

load_dotenv()

# API Credentials
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")

# Target
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS")

# Endpoints
RTDS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
DATA_API_URL = "https://data-api.polymarket.com"
GAMMA_API_URL = "https://gamma-api.polymarket.com"
CLOB_API_URL = "https://clob.polymarket.com"

# Configuration
CHAIN_ID = 137  # Polygon Mainnet
RPC_URL = os.getenv("RPC_URL", "https://polygon-rpc.com")
