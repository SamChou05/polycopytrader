"""
Wallets API - CRUD operations for tracked wallet addresses.
"""

from flask import Blueprint, request, jsonify
from database import get_database
from logger import get_logger

wallets_bp = Blueprint('wallets', __name__)
logger = get_logger('api.wallets')


@wallets_bp.route('/wallets', methods=['GET'])
def list_wallets():
    """Get all tracked wallets."""
    try:
        db = get_database()
        wallets = db.get_all_wallets()
        return jsonify([
            {
                'id': w.id,
                'address': w.address,
                'name': w.name,
                'description': w.description,
                'username': w.username,
                'enabled': w.enabled,
                'created_at': w.created_at,
            }
            for w in wallets
        ])
    except Exception as e:
        logger.error(f"Error listing wallets: {e}")
        return jsonify({'error': str(e)}), 500


@wallets_bp.route('/wallets', methods=['POST'])
def add_wallet():
    """Add a new wallet to track."""
    try:
        data = request.get_json()
        address = data.get('address')
        name = data.get('name', '')
        description = data.get('description', '')
        username = data.get('username')  # Can be auto-fetched or manual
        
        if not address:
            return jsonify({'error': 'Address is required'}), 400
        
        # Auto-fetch username from Polymarket if not provided
        if not username and not name:
            from utils import get_user_profile
            profile = get_user_profile(address)
            if profile and profile.get('username'):
                username = profile.get('username')
                name = username  # Use username as default name
        
        if not name:
            name = f"Wallet {address[:8]}..."
        
        db = get_database()
        wallet = db.add_wallet(address, name, description, username)
        
        if wallet:
            logger.info(f"Added wallet: {name} ({address[:10]}...)")
            return jsonify({
                'id': wallet.id,
                'address': wallet.address,
                'name': wallet.name,
                'description': wallet.description,
                'username': wallet.username,
                'enabled': wallet.enabled,
            }), 201
        else:
            return jsonify({'error': 'Wallet already exists'}), 409
    except Exception as e:
        logger.error(f"Error adding wallet: {e}")
        return jsonify({'error': str(e)}), 500


@wallets_bp.route('/wallets/<address>', methods=['GET'])
def get_wallet(address: str):
    """Get a specific wallet by address."""
    try:
        db = get_database()
        wallet = db.get_wallet(address)
        
        if wallet:
            return jsonify({
                'id': wallet.id,
                'address': wallet.address,
                'name': wallet.name,
                'enabled': wallet.enabled,
                'created_at': wallet.created_at,
            })
        else:
            return jsonify({'error': 'Wallet not found'}), 404
    except Exception as e:
        logger.error(f"Error getting wallet: {e}")
        return jsonify({'error': str(e)}), 500


@wallets_bp.route('/wallets/<address>', methods=['PATCH'])
def update_wallet(address: str):
    """Update wallet properties (name, enabled)."""
    try:
        data = request.get_json()
        db = get_database()
        
        # Update name if provided
        if 'name' in data:
            db.update_wallet_name(address, data['name'])
        
        # Update enabled status if provided
        if 'enabled' in data:
            db.set_wallet_enabled(address, data['enabled'])
        
        # Return updated wallet
        wallet = db.get_wallet(address)
        if wallet:
            return jsonify({
                'id': wallet.id,
                'address': wallet.address,
                'name': wallet.name,
                'enabled': wallet.enabled,
            })
        else:
            return jsonify({'error': 'Wallet not found'}), 404
    except Exception as e:
        logger.error(f"Error updating wallet: {e}")
        return jsonify({'error': str(e)}), 500


@wallets_bp.route('/wallets/<address>', methods=['DELETE'])
def delete_wallet(address: str):
    """Delete a wallet from tracking."""
    try:
        db = get_database()
        success = db.delete_wallet(address)
        
        if success:
            logger.info(f"Deleted wallet: {address[:10]}...")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Wallet not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting wallet: {e}")
        return jsonify({'error': str(e)}), 500


@wallets_bp.route('/wallets/<address>/toggle', methods=['POST'])
def toggle_wallet(address: str):
    """Toggle wallet enabled/disabled status."""
    try:
        db = get_database()
        wallet = db.get_wallet(address)
        
        if not wallet:
            return jsonify({'error': 'Wallet not found'}), 404
        
        new_status = not wallet.enabled
        db.set_wallet_enabled(address, new_status)
        
        return jsonify({
            'address': address,
            'enabled': new_status,
        })
    except Exception as e:
        logger.error(f"Error toggling wallet: {e}")
        return jsonify({'error': str(e)}), 500
