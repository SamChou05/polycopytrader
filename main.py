import time
import sys
import logging
from config import TARGET_ADDRESS, API_KEY, API_SECRET, API_PASSPHRASE, PRIVATE_KEY
from utils import get_user_profile, is_valid_address
from monitor import Monitor
from rule_engine import RuleEngine
from executor import Executor

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

    # 1. Validate Target Address
    target = TARGET_ADDRESS
    if not target:
        logging.error("TARGET_ADDRESS not set in .env")
        return

    if not is_valid_address(target):
        logging.error(f"Invalid target address: {target}")
        return

    logging.info(f"Target Address: {target}")
    
    # 2. Fetch Target Profile
    profile = get_user_profile(target)
    if profile:
        logging.info(f"Target Profile: {profile.get('name', 'Unknown')} ({profile.get('bio', '')})")
    else:
        logging.warning("Could not fetch target profile.")

    # 3. Initialize Components
    # Configuration for Rule Engine (could be loaded from env or args)
    rule_config = {
        'mode': 'percentage',
        'percentage': 0.1, # Copy 10% of target size
        'min_size': 5.0 # Minimum 5 USDC
    }
    rule_engine = RuleEngine(rule_config)
    
    # Initialize Executor (Dry Run by default for safety)
    executor = Executor(dry_run=True)
    if API_KEY and API_SECRET and API_PASSPHRASE:
        executor.set_api_creds(API_KEY, API_SECRET, API_PASSPHRASE)
    else:
        logging.warning("API credentials not fully set. Executor might fail on real orders.")

    # 4. Define Trade Callback
    def on_trade_detected(trade):
        logging.info(f"Trade Detected: {trade}")
        
        # Calculate Size
        try:
            # For percentage mode, we only need target trade size
            target_size = trade.get('size')
            if not target_size:
                logging.warning("Trade missing size info")
                return

            copier_size = rule_engine.calculate_size(target_size)
            
            # Apply Constraints (Min Tick, Min Size)
            # Note: Min tick depends on market. Ideally we fetch market info here.
            # For now assuming 0.01 tick size or similar generic handling
            final_size = rule_engine.apply_constraints(copier_size, min_tick_size=0.01)
            
            if final_size == 0:
                logging.info(f"Calculated size {copier_size} below minimum. Skipping.")
                return

            logging.info(f"Placing Order: Size={final_size} (Target={target_size})")
            
            # Place Order
            # Need to map trade details to order args
            # This requires more robust asset/token ID mapping from the event
            token_id = trade.get('asset') 
            side = 'BUY' if trade.get('side') == 'BUY' else 'SELL'
            price = trade.get('price') # Limit price
            
            result = executor.place_order(token_id, side, price, float(final_size))
            logging.info(f"Order Result: {result}")

        except Exception as e:
            logging.error(f"Error processing trade: {e}")

    # 5. Start Monitor
    monitor = Monitor(target, on_trade_detected)
    logging.info("Starting Monitor Service...")
    monitor.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping...")
        monitor.stop()

if __name__ == "__main__":
    main()
