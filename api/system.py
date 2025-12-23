"""
System API - Health checks, connection status, and system info.
"""

from flask import Blueprint, jsonify
from database import get_database
from logger import get_logger

system_bp = Blueprint('system', __name__)
logger = get_logger('api.system')


@system_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'polymarket-terminal',
    })


@system_bp.route('/status', methods=['GET'])
def get_status():
    """Get system status including connection info."""
    try:
        db = get_database()
        wallets = db.get_all_wallets()
        active_wallets = [w for w in wallets if w.enabled]
        
        return jsonify({
            'connected': True,  # TODO: Check actual monitor connection
            'mode': 'DRY_RUN',  # TODO: Get from settings
            'wallets_total': len(wallets),
            'wallets_active': len(active_wallets),
            'database': 'connected',
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({
            'connected': False,
            'error': str(e),
        }), 500


@system_bp.route('/info', methods=['GET'])
def get_info():
    """Get system information."""
    return jsonify({
        'name': 'Polymarket Terminal',
        'version': '0.1.0',
        'features': [
            'copy-trader',
            'wallet-tracking',
            'trade-history',
        ],
        'api_version': 'v1',
    })
