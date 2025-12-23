import time
import sys
import logging
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

    # 2. Initialize Components
    rule_config = {
        'mode': 'percentage',
        'percentage': 0.1,  # Copy 10% of target size
        'min_size': 5.0     # Minimum 5 USDC
    }
    rule_engine = RuleEngine(rule_config)
    
    # Initialize Executor (Dry Run by default for safety)
    executor = Executor(dry_run=True)
    if API_KEY and API_SECRET and API_PASSPHRASE:
        executor.set_api_creds(API_KEY, API_SECRET, API_PASSPHRASE)
    else:
        logging.warning("API credentials not fully set. Running in DRY RUN mode.")

    # 3. Define Trade Callback - saves ALL trades to database
    def on_trade_detected(trade):
        logging.info(f"Trade Detected: {trade}")
        
        copied = False
        copier_size = 0
        
        try:
            target_size = trade.get('size')
            if not target_size:
                logging.warning("Trade missing size info")
            else:
                copier_size = rule_engine.calculate_size(target_size)
                final_size = rule_engine.apply_constraints(copier_size, min_tick_size=0.01)
                
                if final_size == 0:
                    logging.info(f"Calculated size {copier_size} below minimum. Skipping copy.")
                else:
                    logging.info(f"Placing Order: Size={final_size} (Target={target_size})")
                    
                    token_id = trade.get('asset')
                    side = 'BUY' if trade.get('side') == 'BUY' else 'SELL'
                    price = trade.get('price')
                    
                    result = executor.place_order(token_id, side, price, float(final_size))
                    logging.info(f"Order Result: {result}")
                    copied = True
                    copier_size = final_size

        except Exception as e:
            logging.error(f"Error processing trade: {e}")
        
        # 4. ALWAYS save trade to database (copied or not)
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
                timestamp=datetime.now().isoformat()
            )
            db.add_trade(trade_record)
            logging.info(f"Trade saved to database (copied={copied})")
        except Exception as e:
            logging.error(f"Error saving trade to database: {e}")

    # 5. Start monitors for all wallets
    monitors = []
    for wallet in wallets:
        if not is_valid_address(wallet.address):
            logging.error(f"Invalid address for {wallet.name}: {wallet.address}")
            continue
            
        monitor = Monitor(wallet.address, on_trade_detected)
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
