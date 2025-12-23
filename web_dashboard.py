"""
Web-based Dashboard for Polymarket Copy Trader
Flask + Socket.IO for real-time updates
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import threading
import time
import logging

from config import TARGET_ADDRESS, API_KEY, API_SECRET, API_PASSPHRASE
from utils import get_user_profile, is_valid_address
from monitor import Monitor
from rule_engine import RuleEngine
from executor import Executor

# Suppress Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'polymarket-copy-trader'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
state = {
    'connected': False,
    'target_address': '',
    'target_name': 'Unknown',
    'mode': 'DRY RUN',
    'start_time': datetime.now().isoformat(),
    'trades': [],
    'stats': {
        'trades_detected': 0,
        'trades_copied': 0,
        'trades_skipped': 0,
        'avg_latency': 0,
        'total_latency': 0
    }
}

monitor = None
rule_engine = None
executor = None


def add_trade(trade, copied=False):
    """Add a trade to state and broadcast to clients."""
    trade_data = {
        'time': datetime.now().strftime('%H:%M:%S'),
        'title': trade.get('title', 'Unknown')[:25],
        'outcome': trade.get('outcome', '?')[:15],
        'side': trade.get('side', 'BUY'),
        'size': round(trade.get('size', 0), 2),
        'price': round(trade.get('price', 0), 4),
        'latency': trade.get('latency_ms', 0),
        'copied': copied
    }
    
    state['trades'].insert(0, trade_data)
    state['trades'] = state['trades'][:15]  # Keep last 15
    state['stats']['trades_detected'] += 1
    
    if trade.get('latency_ms'):
        state['stats']['total_latency'] += trade['latency_ms']
        state['stats']['avg_latency'] = state['stats']['total_latency'] // state['stats']['trades_detected']
    
    if copied:
        state['stats']['trades_copied'] += 1
    else:
        state['stats']['trades_skipped'] += 1
    
    # Broadcast update to all connected clients
    socketio.emit('trade_update', {'trade': trade_data, 'stats': state['stats']})


def on_trade_detected(trade):
    """Callback when monitor detects a trade."""
    try:
        target_size = trade.get('size')
        if not target_size:
            add_trade(trade, copied=False)
            return

        copier_size = rule_engine.calculate_size(target_size)
        final_size = rule_engine.apply_constraints(copier_size, min_tick_size=0.01)
        
        if final_size == 0:
            add_trade(trade, copied=False)
            return

        token_id = trade.get('asset')
        side = trade.get('side', 'BUY')
        price = trade.get('price')
        
        result = executor.place_order(token_id, side, price, float(final_size))
        add_trade(trade, copied=bool(result))

    except Exception as e:
        print(f"Error processing trade: {e}")
        add_trade(trade, copied=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/state')
def get_state():
    return jsonify(state)


@socketio.on('connect')
def handle_connect():
    emit('initial_state', state)


def start_monitor():
    global monitor, state
    target = TARGET_ADDRESS
    
    if not target or not is_valid_address(target):
        print("Invalid TARGET_ADDRESS")
        return
    
    profile = get_user_profile(target)
    state['target_name'] = profile.get('name', profile.get('pseudonym', 'Unknown')) if profile else "Unknown"
    state['target_address'] = target
    
    monitor = Monitor(target, on_trade_detected)
    monitor.start()
    state['connected'] = True
    
    # Notify clients
    socketio.emit('connection_status', {'connected': True})


def run_app():
    global rule_engine, executor
    
    # Initialize components
    rule_engine = RuleEngine({
        'mode': 'percentage',
        'percentage': 0.1,
        'min_size': 0.1
    })
    executor = Executor(dry_run=True)
    
    if API_KEY and API_SECRET and API_PASSPHRASE:
        executor.set_api_creds(API_KEY, API_SECRET, API_PASSPHRASE)
    
    # Start monitor in background
    monitor_thread = threading.Thread(target=start_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    print("\n" + "="*50)
    print("🚀 POLYMARKET COPY TRADER - WEB DASHBOARD")
    print("="*50)
    print(f"📍 Open in browser: http://localhost:5001")
    print("="*50 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_app()
