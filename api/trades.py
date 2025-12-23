"""
Trades API - Trade history and statistics.
"""

from flask import Blueprint, request, jsonify
from database import get_database
from logger import get_logger

trades_bp = Blueprint('trades', __name__)
logger = get_logger('api.trades')


@trades_bp.route('/trades', methods=['GET'])
def list_trades():
    """Get trade history with optional filtering."""
    try:
        # Query params
        limit = request.args.get('limit', 50, type=int)
        wallet = request.args.get('wallet')
        copied_only = request.args.get('copied', type=bool)
        
        db = get_database()
        
        if wallet:
            trades = db.get_trades(wallet_address=wallet, limit=limit)
        else:
            trades = db.get_trades(limit=limit)
        
        # Filter if needed
        if copied_only is not None:
            trades = [t for t in trades if t.copied == copied_only]
        
        return jsonify([
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
        ])
    except Exception as e:
        logger.error(f"Error listing trades: {e}")
        return jsonify({'error': str(e)}), 500


@trades_bp.route('/trades/<int:trade_id>', methods=['GET'])
def get_trade(trade_id: int):
    """Get a specific trade by ID."""
    try:
        db = get_database()
        trades = db.get_trades(limit=1000)
        
        trade = next((t for t in trades if t.id == trade_id), None)
        
        if trade:
            return jsonify({
                'id': trade.id,
                'wallet_address': trade.wallet_address,
                'asset': trade.asset,
                'side': trade.side,
                'size': trade.size,
                'price': trade.price,
                'copied': trade.copied,
                'latency_ms': trade.latency_ms,
                'title': trade.title,
                'outcome': trade.outcome,
                'timestamp': trade.timestamp,
            })
        else:
            return jsonify({'error': 'Trade not found'}), 404
    except Exception as e:
        logger.error(f"Error getting trade: {e}")
        return jsonify({'error': str(e)}), 500


@trades_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get trading statistics."""
    try:
        db = get_database()
        stats = db.get_stats()
        
        return jsonify({
            'trades_detected': stats.get('total_trades', 0),
            'trades_copied': stats.get('copied_trades', 0),
            'trades_skipped': stats.get('skipped_trades', 0),
            'avg_latency': stats.get('avg_latency', 0),
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500


@trades_bp.route('/stats/by-wallet', methods=['GET'])
def get_stats_by_wallet():
    """Get statistics grouped by tracked wallet."""
    try:
        db = get_database()
        wallets = db.get_all_wallets()
        
        stats_by_wallet = []
        for wallet in wallets:
            trades = db.get_trades(wallet_address=wallet.address, limit=1000)
            
            if trades:
                stats_by_wallet.append({
                    'address': wallet.address,
                    'name': wallet.name,
                    'total_trades': len(trades),
                    'copied_trades': sum(1 for t in trades if t.copied),
                    'total_volume': sum(t.size * t.price for t in trades),
                })
        
        return jsonify(stats_by_wallet)
    except Exception as e:
        logger.error(f"Error getting wallet stats: {e}")
        return jsonify({'error': str(e)}), 500
