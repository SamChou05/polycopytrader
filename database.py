"""
SQLite Database Layer for the Polymarket Copy Trader.
Manages wallets, settings, and trade history with proper CRUD operations.
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from logger import get_database_logger
from exceptions import (
    DatabaseConnectionError,
    RecordNotFoundError,
    DuplicateRecordError,
)

logger = get_database_logger()

# Database file path
DB_PATH = Path(__file__).parent / "copy_trader.db"


# ============================================
# Data Classes (Models)
# ============================================

@dataclass
class Wallet:
    """Represents a tracked wallet."""
    id: Optional[int]
    address: str
    name: str
    enabled: bool = True
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "address": self.address,
            "name": self.name,
            "enabled": self.enabled,
            "created_at": self.created_at,
        }


@dataclass
class Setting:
    """Represents a configuration setting."""
    key: str
    value: str
    category: str = "general"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "category": self.category,
        }


@dataclass
class TradeRecord:
    """Represents a trade in history."""
    id: Optional[int]
    wallet_address: str
    asset: str
    side: str
    size: float
    price: float
    copied: bool
    latency_ms: Optional[int]
    title: Optional[str]
    outcome: Optional[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "wallet_address": self.wallet_address,
            "asset": self.asset,
            "side": self.side,
            "size": self.size,
            "price": self.price,
            "copied": self.copied,
            "latency_ms": self.latency_ms,
            "title": self.title,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
        }


# ============================================
# Database Connection Manager
# ============================================

class Database:
    """SQLite database manager with connection pooling and CRUD operations."""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_schema()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
        finally:
            if conn:
                conn.close()
    
    def _init_schema(self):
        """Initialize database schema if not exists."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Wallets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general'
                )
            """)
            
            # Trade history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wallet_address TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    side TEXT NOT NULL,
                    size REAL NOT NULL,
                    price REAL NOT NULL,
                    copied INTEGER NOT NULL,
                    latency_ms INTEGER,
                    title TEXT,
                    outcome TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_history_wallet 
                ON trade_history(wallet_address)
            """)
            
            conn.commit()
            logger.info("Database schema initialized")
    
    # ============================================
    # Wallet Operations
    # ============================================
    
    def add_wallet(self, address: str, name: str, enabled: bool = True) -> Wallet:
        """Add a new wallet to track."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO wallets (address, name, enabled) VALUES (?, ?, ?)",
                    (address.lower(), name, int(enabled))
                )
                conn.commit()
                wallet_id = cursor.lastrowid
                logger.info(f"Added wallet: {name} ({address[:8]}...)")
                return Wallet(
                    id=wallet_id,
                    address=address.lower(),
                    name=name,
                    enabled=enabled
                )
            except sqlite3.IntegrityError:
                raise DuplicateRecordError(f"Wallet {address} already exists")
    
    def get_wallet(self, address: str) -> Optional[Wallet]:
        """Get a wallet by address."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM wallets WHERE address = ?",
                (address.lower(),)
            )
            row = cursor.fetchone()
            if row:
                return Wallet(
                    id=row["id"],
                    address=row["address"],
                    name=row["name"],
                    enabled=bool(row["enabled"]),
                    created_at=row["created_at"]
                )
            return None
    
    def get_all_wallets(self, enabled_only: bool = False) -> List[Wallet]:
        """Get all tracked wallets."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if enabled_only:
                cursor.execute("SELECT * FROM wallets WHERE enabled = 1")
            else:
                cursor.execute("SELECT * FROM wallets")
            rows = cursor.fetchall()
            return [
                Wallet(
                    id=row["id"],
                    address=row["address"],
                    name=row["name"],
                    enabled=bool(row["enabled"]),
                    created_at=row["created_at"]
                )
                for row in rows
            ]
    
    def update_wallet(self, address: str, name: str = None, enabled: bool = None) -> bool:
        """Update wallet properties."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if enabled is not None:
                updates.append("enabled = ?")
                params.append(int(enabled))
            
            if not updates:
                return False
            
            params.append(address.lower())
            cursor.execute(
                f"UPDATE wallets SET {', '.join(updates)} WHERE address = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_wallet(self, address: str) -> bool:
        """Remove a wallet from tracking."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM wallets WHERE address = ?",
                (address.lower(),)
            )
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Deleted wallet: {address[:8]}...")
                return True
            return False
    
    # ============================================
    # Settings Operations
    # ============================================
    
    def set_setting(self, key: str, value: Any, category: str = "general") -> None:
        """Set a configuration value (upsert)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Convert non-string values to JSON
            if not isinstance(value, str):
                value = json.dumps(value)
            cursor.execute(
                """INSERT INTO settings (key, value, category) 
                   VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value = ?, category = ?""",
                (key, value, category, value, category)
            )
            conn.commit()
            logger.debug(f"Setting updated: {key} = {value}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                value = row["value"]
                # Try to parse JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return default
    
    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT key, value FROM settings WHERE category = ?",
                (category,)
            )
            rows = cursor.fetchall()
            result = {}
            for row in rows:
                try:
                    result[row["key"]] = json.loads(row["value"])
                except (json.JSONDecodeError, TypeError):
                    result[row["key"]] = row["value"]
            return result
    
    def delete_setting(self, key: str) -> bool:
        """Delete a setting."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM settings WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ============================================
    # Trade History Operations
    # ============================================
    
    def add_trade(self, trade: TradeRecord) -> int:
        """Record a trade in history."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO trade_history 
                   (wallet_address, asset, side, size, price, copied, 
                    latency_ms, title, outcome, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trade.wallet_address.lower(),
                    trade.asset,
                    trade.side,
                    trade.size,
                    trade.price,
                    int(trade.copied),
                    trade.latency_ms,
                    trade.title,
                    trade.outcome,
                    trade.timestamp or datetime.now().isoformat()
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_trades(
        self, 
        wallet_address: str = None, 
        limit: int = 50,
        offset: int = 0
    ) -> List[TradeRecord]:
        """Get trade history, optionally filtered by wallet."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if wallet_address:
                cursor.execute(
                    """SELECT * FROM trade_history 
                       WHERE wallet_address = ?
                       ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
                    (wallet_address.lower(), limit, offset)
                )
            else:
                cursor.execute(
                    """SELECT * FROM trade_history 
                       ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
                    (limit, offset)
                )
            rows = cursor.fetchall()
            return [
                TradeRecord(
                    id=row["id"],
                    wallet_address=row["wallet_address"],
                    asset=row["asset"],
                    side=row["side"],
                    size=row["size"],
                    price=row["price"],
                    copied=bool(row["copied"]),
                    latency_ms=row["latency_ms"],
                    title=row["title"],
                    outcome=row["outcome"],
                    timestamp=row["timestamp"]
                )
                for row in rows
            ]
    
    def get_stats(self, wallet_address: str = None) -> Dict[str, Any]:
        """Get aggregated statistics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            where = "WHERE wallet_address = ?" if wallet_address else ""
            params = (wallet_address.lower(),) if wallet_address else ()
            
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN copied = 1 THEN 1 ELSE 0 END) as copied_trades,
                    AVG(latency_ms) as avg_latency
                FROM trade_history {where}
            """, params)
            
            row = cursor.fetchone()
            return {
                "total_trades": row["total_trades"] or 0,
                "copied_trades": row["copied_trades"] or 0,
                "skipped_trades": (row["total_trades"] or 0) - (row["copied_trades"] or 0),
                "avg_latency": round(row["avg_latency"] or 0, 2)
            }


# Singleton instance
_db_instance = None

def get_database() -> Database:
    """Get the singleton database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
