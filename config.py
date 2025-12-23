"""
Configuration management for Polymarket Copy Trader.
Secrets (keys) from .env, other settings from SQLite database.
"""

import os
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()


# ============================================
# Secrets (from environment only)
# ============================================

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")
RPC_URL = os.getenv("RPC_URL", "https://polygon-rpc.com")


# ============================================
# API Endpoints (constants)
# ============================================

RTDS_URL = "wss://ws-live-data.polymarket.com"
DATA_API_URL = "https://data-api.polymarket.com"
GAMMA_API_URL = "https://gamma-api.polymarket.com"
CLOB_API_URL = "https://clob.polymarket.com"


# ============================================
# Chain Configuration
# ============================================

CHAIN_ID = 137  # Polygon Mainnet


# ============================================
# Dynamic Settings (from database with defaults)
# ============================================

# Default values (used if database is empty)
DEFAULT_SETTINGS = {
    "copy_trader": {
        "mode": "percentage",
        "percentage": 0.1,
        "min_size": 0.1,
        "dry_run": True,
        "execution_mode": "alert",  # "alert" or "execute"
    }
}


def get_setting(key: str, category: str = "general", default: Any = None) -> Any:
    """
    Get a setting from the database, with fallback to defaults.
    Lazy-loads database to avoid circular imports.
    """
    try:
        from database import get_database
        db = get_database()
        value = db.get_setting(key)
        if value is not None:
            return value
    except Exception:
        pass  # Database not available, use defaults
    
    # Check default settings
    if category in DEFAULT_SETTINGS and key in DEFAULT_SETTINGS[category]:
        return DEFAULT_SETTINGS[category][key]
    
    return default


def set_setting(key: str, value: Any, category: str = "general") -> None:
    """Set a setting in the database."""
    try:
        from database import get_database
        db = get_database()
        db.set_setting(key, value, category)
    except Exception as e:
        from logger import logger
        logger.warning(f"Could not save setting {key}: {e}")


# ============================================
# Legacy support (for backward compatibility)
# ============================================

# TARGET_ADDRESS now comes from database, but support .env fallback
_env_target = os.getenv("TARGET_ADDRESS")

def get_target_addresses() -> list[str]:
    """
    Get list of target addresses to monitor.
    Returns addresses from database if available, else from .env.
    """
    try:
        from database import get_database
        db = get_database()
        wallets = db.get_all_wallets(enabled_only=True)
        if wallets:
            return [w.address for w in wallets]
    except Exception:
        pass
    
    # Fallback to .env
    if _env_target:
        return [_env_target.lower()]
    return []


# For backward compatibility with existing code
TARGET_ADDRESS = _env_target

