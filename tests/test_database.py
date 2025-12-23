"""
Unit tests for the database module.
Tests CRUD operations for wallets, settings, and trade history.
"""

import os
import pytest
from pathlib import Path
from datetime import datetime

# Use a temporary test database
TEST_DB_PATH = Path(__file__).parent.parent / "test_copy_trader.db"

# Patch DB_PATH before importing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now we need to set up the database module to use test DB
import database
database.DB_PATH = TEST_DB_PATH

from database import (
    Database,
    Wallet,
    Setting,
    TradeRecord,
    get_database,
)
from exceptions import DuplicateRecordError


@pytest.fixture
def db():
    """Create a fresh test database for each test."""
    # Remove existing test DB
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)
    
    # Create new database instance
    test_db = Database(TEST_DB_PATH)
    yield test_db
    
    # Cleanup
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)


class TestWalletOperations:
    """Test wallet CRUD operations."""
    
    def test_add_wallet(self, db):
        """Test adding a new wallet."""
        wallet = db.add_wallet(
            address="0x1234567890abcdef1234567890abcdef12345678",
            name="Test Wallet"
        )
        
        assert wallet.id is not None
        assert wallet.address == "0x1234567890abcdef1234567890abcdef12345678"
        assert wallet.name == "Test Wallet"
        assert wallet.enabled is True
    
    def test_add_duplicate_wallet_raises_error(self, db):
        """Test that adding a duplicate wallet raises DuplicateRecordError."""
        db.add_wallet(address="0xABCDEF", name="First")
        
        with pytest.raises(DuplicateRecordError):
            db.add_wallet(address="0xabcdef", name="Second")  # Case insensitive
    
    def test_get_wallet(self, db):
        """Test retrieving a wallet by address."""
        db.add_wallet(address="0x123", name="My Wallet")
        
        wallet = db.get_wallet("0x123")
        
        assert wallet is not None
        assert wallet.name == "My Wallet"
    
    def test_get_wallet_not_found(self, db):
        """Test that get_wallet returns None for non-existent address."""
        wallet = db.get_wallet("0xnonexistent")
        assert wallet is None
    
    def test_get_all_wallets(self, db):
        """Test retrieving all wallets."""
        db.add_wallet(address="0x111", name="Wallet 1")
        db.add_wallet(address="0x222", name="Wallet 2")
        db.add_wallet(address="0x333", name="Wallet 3", enabled=False)
        
        all_wallets = db.get_all_wallets()
        enabled_wallets = db.get_all_wallets(enabled_only=True)
        
        assert len(all_wallets) == 3
        assert len(enabled_wallets) == 2
    
    def test_update_wallet(self, db):
        """Test updating wallet properties."""
        db.add_wallet(address="0x123", name="Original")
        
        db.update_wallet(address="0x123", name="Updated", enabled=False)
        
        wallet = db.get_wallet("0x123")
        assert wallet.name == "Updated"
        assert wallet.enabled is False
    
    def test_delete_wallet(self, db):
        """Test deleting a wallet."""
        db.add_wallet(address="0x123", name="To Delete")
        
        result = db.delete_wallet("0x123")
        
        assert result is True
        assert db.get_wallet("0x123") is None


class TestSettingsOperations:
    """Test settings CRUD operations."""
    
    def test_set_and_get_string_setting(self, db):
        """Test setting and getting a string value."""
        db.set_setting("theme", "dark")
        
        value = db.get_setting("theme")
        
        assert value == "dark"
    
    def test_set_and_get_json_setting(self, db):
        """Test setting and getting a complex JSON value."""
        config = {"percentage": 0.1, "min_size": 5.0}
        db.set_setting("copy_trader_config", config, category="copy_trader")
        
        value = db.get_setting("copy_trader_config")
        
        assert value == config
        assert value["percentage"] == 0.1
    
    def test_get_setting_default(self, db):
        """Test default value for non-existent setting."""
        value = db.get_setting("nonexistent", default="fallback")
        assert value == "fallback"
    
    def test_get_settings_by_category(self, db):
        """Test getting all settings in a category."""
        db.set_setting("key1", "value1", category="test")
        db.set_setting("key2", "value2", category="test")
        db.set_setting("other", "other", category="other")
        
        settings = db.get_settings_by_category("test")
        
        assert len(settings) == 2
        assert settings["key1"] == "value1"
        assert settings["key2"] == "value2"
    
    def test_upsert_setting(self, db):
        """Test that set_setting updates existing values."""
        db.set_setting("key", "original")
        db.set_setting("key", "updated")
        
        value = db.get_setting("key")
        
        assert value == "updated"


class TestTradeHistoryOperations:
    """Test trade history operations."""
    
    def test_add_trade(self, db):
        """Test adding a trade record."""
        trade = TradeRecord(
            id=None,
            wallet_address="0x123",
            asset="0xabc",
            side="BUY",
            size=10.0,
            price=0.55,
            copied=True,
            latency_ms=150,
            title="Test Market",
            outcome="Yes",
            timestamp=datetime.now().isoformat()
        )
        
        trade_id = db.add_trade(trade)
        
        assert trade_id is not None
        assert trade_id > 0
    
    def test_get_trades(self, db):
        """Test retrieving trade history."""
        for i in range(5):
            trade = TradeRecord(
                id=None,
                wallet_address="0x123",
                asset=f"0xasset{i}",
                side="BUY",
                size=10.0,
                price=0.5,
                copied=True,
                latency_ms=100,
                title=f"Market {i}",
                outcome="Yes",
                timestamp=datetime.now().isoformat()
            )
            db.add_trade(trade)
        
        trades = db.get_trades(limit=3)
        
        assert len(trades) == 3
    
    def test_get_trades_by_wallet(self, db):
        """Test filtering trades by wallet address."""
        for addr in ["0x111", "0x222", "0x111"]:
            trade = TradeRecord(
                id=None,
                wallet_address=addr,
                asset="0xabc",
                side="BUY",
                size=10.0,
                price=0.5,
                copied=True,
                latency_ms=100,
                title="Market",
                outcome="Yes",
                timestamp=datetime.now().isoformat()
            )
            db.add_trade(trade)
        
        trades = db.get_trades(wallet_address="0x111")
        
        assert len(trades) == 2
    
    def test_get_stats(self, db):
        """Test aggregated statistics."""
        for i in range(5):
            trade = TradeRecord(
                id=None,
                wallet_address="0x123",
                asset="0xabc",
                side="BUY",
                size=10.0,
                price=0.5,
                copied=(i % 2 == 0),  # 3 copied, 2 not
                latency_ms=100 + i * 10,  # 100, 110, 120, 130, 140
                title="Market",
                outcome="Yes",
                timestamp=datetime.now().isoformat()
            )
            db.add_trade(trade)
        
        stats = db.get_stats()
        
        assert stats["total_trades"] == 5
        assert stats["copied_trades"] == 3
        assert stats["skipped_trades"] == 2
        assert stats["avg_latency"] == 120.0  # Average of 100-140


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
