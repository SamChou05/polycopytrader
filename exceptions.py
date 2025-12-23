"""
Custom exceptions for the Polymarket Copy Trader application.
Provides clear error handling with specific exception types.
"""


class CopyTraderError(Exception):
    """Base exception for all Copy Trader errors."""
    pass


# ============================================
# Configuration Errors
# ============================================

class ConfigurationError(CopyTraderError):
    """Raised when there's a configuration issue."""
    pass


class MissingCredentialsError(ConfigurationError):
    """Raised when required credentials are missing."""
    pass


class InvalidAddressError(ConfigurationError):
    """Raised when an Ethereum address is invalid."""
    pass


# ============================================
# Database Errors
# ============================================

class DatabaseError(CopyTraderError):
    """Base exception for database operations."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class RecordNotFoundError(DatabaseError):
    """Raised when a requested record doesn't exist."""
    pass


class DuplicateRecordError(DatabaseError):
    """Raised when trying to create a duplicate record."""
    pass


# ============================================
# Monitor Errors
# ============================================

class MonitorError(CopyTraderError):
    """Base exception for monitoring operations."""
    pass


class WebSocketConnectionError(MonitorError):
    """Raised when WebSocket connection fails."""
    pass


class APIRateLimitError(MonitorError):
    """Raised when API rate limit is exceeded."""
    pass


class InvalidEventError(MonitorError):
    """Raised when an event cannot be parsed."""
    pass


# ============================================
# Execution Errors
# ============================================

class ExecutionError(CopyTraderError):
    """Base exception for order execution."""
    pass


class InsufficientBalanceError(ExecutionError):
    """Raised when wallet has insufficient balance."""
    pass


class OrderRejectedError(ExecutionError):
    """Raised when the exchange rejects an order."""
    pass


class MinSizeError(ExecutionError):
    """Raised when calculated size is below minimum."""
    pass
