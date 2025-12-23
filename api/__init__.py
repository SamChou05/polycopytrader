"""
API Package - Modular Flask Blueprint-based API.

To add a new API module:
1. Create a new file in api/ (e.g., api/markets.py)
2. Create a Blueprint and add routes
3. Import and register in api/__init__.py

Example:
    # api/markets.py
    from flask import Blueprint
    markets_bp = Blueprint('markets', __name__)
    
    @markets_bp.route('/markets')
    def list_markets():
        ...
    
    # api/__init__.py
    from api.markets import markets_bp
    def register_blueprints(app):
        ...
        app.register_blueprint(markets_bp, url_prefix='/api')
"""

from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")


def create_app() -> Flask:
    """Application factory pattern for Flask app."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'  # TODO: Move to env
    
    # Initialize extensions
    socketio.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    return app


def register_blueprints(app: Flask) -> None:
    """Register all API blueprints."""
    from api.wallets import wallets_bp
    from api.settings import settings_bp
    from api.trades import trades_bp
    from api.system import system_bp
    
    app.register_blueprint(wallets_bp, url_prefix='/api')
    app.register_blueprint(settings_bp, url_prefix='/api')
    app.register_blueprint(trades_bp, url_prefix='/api')
    app.register_blueprint(system_bp, url_prefix='/api')
