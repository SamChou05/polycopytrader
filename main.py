import time
import sys
import logging
import json
from datetime import datetime
from config import API_KEY, API_SECRET, API_PASSPHRASE
from utils import is_valid_address
from monitor import Monitor
from rule_engine import RuleEngine
from executor import Executor
from database import get_database, TradeRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("copy_trader.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def load_copy_settings(db):
    """Load copy trading settings from database."""
    settings_str = db.get_setting('copytrader_settings')
    if settings_str:
        try:
            # Handle both string and dict (depending on how it was stored)
            if isinstance(settings_str, dict):
                return settings_str
            return json.loads(settings_str)
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Default settings
    return {
        'liveTrading': False,
        'sizingMode': 'percentage',
        'copyPercentage': 10,
        'fixedAmount': 10,
    }

def get_existing_trade_fingerprints(db, limit=100):
    """Get fingerprints of recent trades to prevent duplicates on restart."""
    trades = db.get_trades(limit=limit)
    fingerprints = set()
    for t in trades:
        # Create same fingerprint format as monitor.py
        # Uses: asset:timestamp:size:price where timestamp is the original trade timestamp
        fingerprint = f"{t.asset}:{t.timestamp}:{t.size}:{t.price}"
        fingerprints.add(fingerprint)
    return fingerprints

def main():
    logging.info("Starting Polymarket Copy Trader...")
    
    # 1. Load wallets from database
    db = get_database()
    wallets = db.get_all_wallets(enabled_only=True)
    
    if not wallets:
        logging.error("No enabled wallets found in database. Add wallets via the web UI.")
        logging.info("Start the web UI with: ./start.sh")
        return
    
    logging.info(f"Loaded {len(wallets)} wallet(s) to monitor:")
    for w in wallets:
        logging.info(f"  - {w.name}: {w.address[:10]}...")
    
    # 2. Get existing trade fingerprints to prevent duplicates on restart
    existing_fingerprints = get_existing_trade_fingerprints(db)
    logging.info(f"Loaded {len(existing_fingerprints)} existing trades for deduplication")
    
    # 2. Load copy trading settings
    settings = load_copy_settings(db)
    live_trading = settings.get('liveTrading', False)
    sizing_mode = settings.get('sizingMode', 'percentage')
    copy_percentage = settings.get('copyPercentage', 10)
    fixed_amount = settings.get('fixedAmount', 10)
    
    logging.info(f"Settings: Live={live_trading}, Mode={sizing_mode}, " +
                 f"Percentage={copy_percentage}%, Fixed=${fixed_amount}")
    
    # 3. Configure Rule Engine based on settings
    if sizing_mode == 'percentage':
        rule_config = {
            'mode': 'percentage',
            'percentage': copy_percentage / 100.0,  # Convert to decimal
            'min_size': 1.0  # Minimum $1 USDC
        }
    else:  # fixed
        rule_config = {
            'mode': 'fixed',
            'fixed_notional': fixed_amount,
            'min_size': 1.0
        }
    rule_engine = RuleEngine(rule_config)
    
    # 4. Initialize Executor (respects live trading setting)
    executor = Executor(dry_run=not live_trading)
    if live_trading and API_KEY and API_SECRET and API_PASSPHRASE:
        executor.set_api_creds(API_KEY, API_SECRET, API_PASSPHRASE)
        logging.info("⚠️  LIVE TRADING ENABLED - Real orders will be placed!")
    elif live_trading:
        logging.warning("Live trading enabled but API credentials not set. Falling back to DRY RUN.")
        executor = Executor(dry_run=True)
    else:
        logging.info("Running in DRY RUN mode (initial state).")

    # 5. Define Trade Callback with hot-reload
    def on_trade_detected(trade):
        # Hot-reload settings from database on each trade
        current_settings = load_copy_settings(db)
        live_trading = current_settings.get('liveTrading', False)
        sizing_mode = current_settings.get('sizingMode', 'percentage')
        copy_percentage = current_settings.get('copyPercentage', 10)
        fixed_amount = current_settings.get('fixedAmount', 10)
        
        logging.info(f"Trade Detected: {trade}")
        logging.info(f"Current settings: Live={live_trading}, Mode={sizing_mode}")
        
        copied = False
        execution_status = 'skipped'
        execution_details = None
        copier_size = 0
        
        # Update executor dry_run state based on current settings
        executor.dry_run = not live_trading
        
        try:
            target_size = trade.get('size')
            target_price = trade.get('price')
            
            if not target_size:
                logging.warning("Trade missing size info")
                execution_status = 'error'
                execution_details = 'Missing size info'
            else:
                # Calculate size based on current settings
                if sizing_mode == 'fixed':
                    copier_size = fixed_amount / target_price if target_price else 0
                else:
                    # Update rule engine on the fly
                    copier_size = target_size * (copy_percentage / 100.0)
                
                # Apply minimum size constraint
                min_size = 1.0
                final_size = round(copier_size, 2) if copier_size >= min_size else 0
                
                if final_size == 0:
                    logging.info(f"Calculated size {copier_size:.4f} below minimum. Skipping copy.")
                    execution_status = 'skipped'
                    execution_details = f'Size {copier_size:.4f} below minimum'
                else:
                    logging.info(f"Placing Order: Size={final_size} (Target={target_size})")
                    
                    token_id = trade.get('asset')
                    side = 'BUY' if trade.get('side') == 'BUY' else 'SELL'
                    price = trade.get('price')
                    
                    if not live_trading:
                        logging.info(f"DRY RUN: Would place {side} {final_size:.4f} @ ${price:.2f}")
                        execution_status = 'dry_run'
                        execution_details = f'Would place {side} {final_size:.4f} @ ${price:.2f}'
                    else:
                        logging.info("⚠️ LIVE: Placing real order...")
                        result = executor.place_order(token_id, side, price, float(final_size))
                        logging.info(f"Order Result: {result}")
                        
                        if result and result.get('success'):
                            copied = True
                            execution_status = 'executed'
                            execution_details = json.dumps(result)
                        else:
                            execution_status = 'failed'
                            execution_details = str(result)
                    
                    copier_size = final_size

        except Exception as e:
            logging.error(f"Error processing trade: {e}")
            execution_status = 'error'
            execution_details = str(e)
        
        # 6. Save trade to database with execution details
        try:
            trade_record = TradeRecord(
                id=None,
                wallet_address=trade.get('wallet_address', ''),
                asset=trade.get('asset', ''),
                side=trade.get('side', ''),
                size=trade.get('size', 0),
                price=trade.get('price', 0),
                copied=copied,
                latency_ms=trade.get('latency_ms'),
                title=trade.get('title'),
                outcome=trade.get('outcome'),
                timestamp=str(trade.get('timestamp', ''))
            )
            db.add_trade(trade_record)
            logging.info(f"Trade saved: status={execution_status}, copied={copied}")
        except Exception as e:
            logging.error(f"Error saving trade to database: {e}")

    # 7. Start monitors for all wallets
    monitors = []
    for wallet in wallets:
        if not is_valid_address(wallet.address):
            logging.error(f"Invalid address for {wallet.name}: {wallet.address}")
            continue
            
        monitor = Monitor(wallet.address, on_trade_detected, initial_fingerprints=existing_fingerprints)
        monitors.append(monitor)
        monitor.start()
        logging.info(f"Started monitoring: {wallet.name}")
    
    if not monitors:
        logging.error("No valid wallets to monitor!")
        return

    logging.info(f"Monitoring {len(monitors)} wallet(s). Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping...")
        for m in monitors:
            m.stop()

if __name__ == "__main__":
    main()

