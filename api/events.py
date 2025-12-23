"""
WebSocket Events - Real-time communication between backend and frontend.
"""

from flask_socketio import emit, join_room, leave_room
from api import socketio
from database import get_database
from logger import get_logger

logger = get_logger('api.events')


@socketio.on('connect')
def handle_connect():
    """Client connected - send initial state."""
    logger.info("Client connected")
    
    try:
        db = get_database()
        
        # Send initial state
        wallets = db.get_all_wallets()
        trades = db.get_trades(limit=20)
        stats = db.get_stats()
        
        emit('initial_state', {
            'wallets': [
                {
                    'id': w.id,
                    'address': w.address,
                    'name': w.name,
                    'enabled': w.enabled,
                }
                for w in wallets
            ],
            'trades': [
                {
                    'id': t.id,
                    'wallet_address': t.wallet_address,
                    'asset': t.asset,
                    'side': t.side,
                    'size': t.size,
                    'price': t.price,
                    'copied': t.copied,
                    'latency_ms': t.latency_ms,
                    'title': t.title,
                    'outcome': t.outcome,
                    'timestamp': t.timestamp,
                }
                for t in trades
            ],
            'stats': stats,
        })
        
        emit('connection_status', {'connected': True})
    except Exception as e:
        logger.error(f"Error on connect: {e}")
        emit('error', {'message': str(e)})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected."""
    logger.info("Client disconnected")


@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to specific channels."""
    channel = data.get('channel')
    if channel:
        join_room(channel)
        logger.info(f"Subscribed to: {channel}")
        emit('subscribed', {'channel': channel})


@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Unsubscribe from specific channels."""
    channel = data.get('channel')
    if channel:
        leave_room(channel)
        logger.info(f"Unsubscribed from: {channel}")


# ============================================
# Helper functions for broadcasting events
# ============================================

def broadcast_trade(trade_data: dict):
    """Broadcast new trade to all connected clients."""
    socketio.emit('trade_update', {
        'trade': trade_data,
    })


def broadcast_stats(stats: dict):
    """Broadcast updated stats."""
    socketio.emit('stats_update', stats)


def broadcast_wallet_update(wallet_data: dict, action: str):
    """Broadcast wallet changes (add/update/delete)."""
    socketio.emit('wallet_update', {
        'action': action,
        'wallet': wallet_data,
    })


def broadcast_alert(alert_data: dict):
    """Broadcast alert notification."""
    socketio.emit('alert', alert_data)
