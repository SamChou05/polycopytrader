#!/usr/bin/env python3
"""
API Server - Entry point for the Polymarket Terminal API.

Run with: python run_api.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import create_app, socketio
from api.events import *  # Register event handlers
from logger import get_logger

logger = get_logger('api.server')


def main():
    """Run the API server."""
    app = create_app()
    
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5001))
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Starting API server on http://{host}:{port}")
    print(f"""
╔════════════════════════════════════════════════════════╗
║         POLYMARKET TERMINAL - API SERVER               ║
╠════════════════════════════════════════════════════════╣
║  API:        http://localhost:{port}/api               ║
║  Health:     http://localhost:{port}/api/health        ║
║  WebSocket:  ws://localhost:{port}/socket.io           ║
╠════════════════════════════════════════════════════════╣
║  Endpoints:                                            ║
║    GET  /api/wallets         - List wallets            ║
║    POST /api/wallets         - Add wallet              ║
║    GET  /api/settings        - List settings           ║
║    PUT  /api/settings/:key   - Set setting             ║
║    GET  /api/trades          - Trade history           ║
║    GET  /api/stats           - Statistics              ║
║    GET  /api/health          - Health check            ║
╚════════════════════════════════════════════════════════╝
    """)
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    main()
