#!/usr/bin/env python3
"""
Dashboard mode entry point for Polymarket Copy Trader.
Run this instead of main.py for the Bloomberg-style terminal dashboard.
"""

import time
import sys
import threading
import logging
from config import TARGET_ADDRESS, API_KEY, API_SECRET, API_PASSPHRASE, PRIVATE_KEY
from utils import get_user_profile, is_valid_address
from monitor import Monitor
from rule_engine import RuleEngine
from executor import Executor
from dashboard import get_dashboard

# Suppress logging when using dashboard (we display info in the UI)
logging.basicConfig(level=logging.WARNING)


def main():
    dashboard = get_dashboard()
    
    # 1. Validate Target Address
    target = TARGET_ADDRESS
    if not target:
        print("ERROR: TARGET_ADDRESS not set in .env")
        return

    if not is_valid_address(target):
        print(f"ERROR: Invalid target address: {target}")
        return

    # 2. Fetch Target Profile
    profile = get_user_profile(target)
    target_name = profile.get('name', profile.get('pseudonym', 'Unknown')) if profile else "Unknown"
    
    dashboard.set_target(target, target_name)
    dashboard.set_mode("DRY RUN")

    # 3. Initialize Components
    rule_config = {
        'mode': 'percentage',
        'percentage': 0.1,
        'min_size': 0.1  # Lower min for testing
    }
    rule_engine = RuleEngine(rule_config)
    executor = Executor(dry_run=True)
    
    if API_KEY and API_SECRET and API_PASSPHRASE:
        executor.set_api_creds(API_KEY, API_SECRET, API_PASSPHRASE)

    # 4. Define Trade Callback
    def on_trade_detected(trade):
        # Add to dashboard
        dashboard.add_trade(trade)
        
        # Calculate Size
        try:
            target_size = trade.get('size')
            if not target_size:
                dashboard.mark_trade_skipped()
                return

            copier_size = rule_engine.calculate_size(target_size)
            final_size = rule_engine.apply_constraints(copier_size, min_tick_size=0.01)
            
            if final_size == 0:
                dashboard.mark_trade_skipped()
                return

            # Place Order
            token_id = trade.get('asset')
            side = trade.get('side', 'BUY')
            price = trade.get('price')
            
            result = executor.place_order(token_id, side, price, float(final_size))
            
            if result:
                dashboard.mark_trade_copied()

        except Exception as e:
            dashboard.mark_trade_skipped()

    # 5. Start Monitor in background thread
    monitor = Monitor(target, on_trade_detected)
    
    def start_monitor():
        monitor.start()
        dashboard.set_connected(True)
    
    monitor_thread = threading.Thread(target=start_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    # Give monitor a moment to connect
    time.sleep(2)
    dashboard.set_connected(True)

    # 6. Run Dashboard (blocking)
    try:
        dashboard.run()
    except KeyboardInterrupt:
        dashboard.stop()
        monitor.stop()


if __name__ == "__main__":
    main()
