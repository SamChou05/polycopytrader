"""
Settings API - Key-value settings storage with category support.
"""

from flask import Blueprint, request, jsonify
from database import get_database
from logger import get_logger

settings_bp = Blueprint('settings', __name__)
logger = get_logger('api.settings')


@settings_bp.route('/settings', methods=['GET'])
def list_settings():
    """Get all settings or filter by category."""
    try:
        category = request.args.get('category')
        db = get_database()
        
        if category:
            # get_settings_by_category returns dict already
            settings_dict = db.get_settings_by_category(category)
            return jsonify(settings_dict)
        else:
            # For all settings, we'd need to get all categories
            # For now, return empty or implement differently
            return jsonify({})
    except Exception as e:
        logger.error(f"Error listing settings: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/settings/<key>', methods=['GET'])
def get_setting(key: str):
    """Get a specific setting value."""
    try:
        db = get_database()
        value = db.get_setting(key)
        
        return jsonify({
            'key': key,
            'value': value,
        })
    except Exception as e:
        logger.error(f"Error getting setting: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/settings/<key>', methods=['PUT'])
def set_setting(key: str):
    """Set or update a setting value."""
    try:
        data = request.get_json()
        value = data.get('value')
        category = data.get('category', 'general')
        
        db = get_database()
        db.set_setting(key, value, category)
        
        logger.info(f"Setting updated: {key}")
        return jsonify({
            'key': key,
            'value': value,
            'category': category,
        })
    except Exception as e:
        logger.error(f"Error setting value: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/settings/<key>', methods=['DELETE'])
def delete_setting(key: str):
    """Delete a setting."""
    try:
        db = get_database()
        success = db.delete_setting(key)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Setting not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting setting: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/settings/bulk', methods=['PUT'])
def bulk_set_settings():
    """Set multiple settings at once."""
    try:
        data = request.get_json()
        settings = data.get('settings', {})
        category = data.get('category', 'general')
        
        db = get_database()
        for key, value in settings.items():
            db.set_setting(key, value, category)
        
        logger.info(f"Bulk updated {len(settings)} settings")
        return jsonify({
            'updated': len(settings),
            'settings': settings,
        })
    except Exception as e:
        logger.error(f"Error bulk setting: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/settings/tool/<tool_id>', methods=['GET'])
def get_tool_settings(tool_id: str):
    """Get all settings for a specific tool."""
    try:
        db = get_database()
        settings = db.get_settings_by_category(f'tool:{tool_id}')
        
        return jsonify({
            s.key: s.value
            for s in settings
        })
    except Exception as e:
        logger.error(f"Error getting tool settings: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/settings/tool/<tool_id>', methods=['PUT'])
def save_tool_settings(tool_id: str):
    """Save all settings for a specific tool."""
    try:
        data = request.get_json()
        settings = data.get('settings', {})
        
        db = get_database()
        category = f'tool:{tool_id}'
        
        for key, value in settings.items():
            db.set_setting(f'{tool_id}:{key}', value, category)
        
        logger.info(f"Saved settings for tool: {tool_id}")
        return jsonify({
            'tool_id': tool_id,
            'settings': settings,
        })
    except Exception as e:
        logger.error(f"Error saving tool settings: {e}")
        return jsonify({'error': str(e)}), 500
