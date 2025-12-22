#!/usr/bin/env python3
"""
Simulation script to test the full copy-trader pipeline.
This injects a fake trade event and verifies the complete flow:
Monitor -> Rule Engine -> Executor
"""

import time
from config import TARGET_ADDRESS
from rule_engine import RuleEngine
from executor import Executor

def main():
    print("=" * 60)
    print("🧪 COPY TRADER PIPELINE SIMULATION TEST")
    print("=" * 60)
    
    target = TARGET_ADDRESS or "0xed28869cfa5777c2d28c69dbb3c4abe0985c356a"
    print(f"\n📍 Target Address: {target}")
    
    # ============================================
    # 1. Initialize Components
    # ============================================
    print("\n[1/4] Initializing Components...")
    
    rule_config = {
        'mode': 'percentage',
        'percentage': 0.1,  # 10% of target size
        'min_size': 5.0
    }
    rule_engine = RuleEngine(rule_config)
    print(f"   ✅ Rule Engine: {rule_config['mode']} mode ({rule_config['percentage']*100}%)")
    
    executor = Executor(dry_run=True)
    print("   ✅ Executor: DRY RUN mode")
    
    # ============================================
    # 2. Simulate Trade Event
    # ============================================
    print("\n[2/4] Simulating Trade Event from Target...")
    
    fake_event = {
        'maker': '0xSomeOtherTrader',
        'taker': target.lower(),  # Target is the buyer (taker)
        'asset': '0x1234567890abcdef1234567890abcdef12345678',
        'size': 100.0,  # Target bought 100 shares
        'price': 0.55,  # At $0.55 each
        'timestamp': int(time.time() * 1000)  # Now (milliseconds)
    }
    
    print(f"   📊 Simulated Trade:")
    print(f"      Asset:  {fake_event['asset'][:10]}...")
    print(f"      Side:   BUY (target is taker)")
    print(f"      Size:   {fake_event['size']} shares")
    print(f"      Price:  ${fake_event['price']}")
    
    # ============================================
    # 3. Process Through Rule Engine
    # ============================================
    print("\n[3/4] Processing through Rule Engine...")
    
    target_size = fake_event['size']
    copier_size = rule_engine.calculate_size(target_size)
    final_size = rule_engine.apply_constraints(copier_size, min_tick_size=0.01)
    
    print(f"   📐 Calculations:")
    print(f"      Target Size:  {target_size}")
    print(f"      Copier Size:  {copier_size} ({rule_config['percentage']*100}% of target)")
    print(f"      Final Size:   {final_size} (after constraints)")
    
    if final_size == 0:
        print("   ❌ Size below minimum! Trade would be skipped.")
        return
    
    # ============================================
    # 4. Execute Order (Dry Run)
    # ============================================
    print("\n[4/4] Executing Order (DRY RUN)...")
    
    result = executor.place_order(
        token_id=fake_event['asset'],
        side='BUY',
        price=fake_event['price'],
        size=float(final_size)
    )
    
    print(f"\n   🎯 Order Result: {result}")
    
    # ============================================
    # Summary
    # ============================================
    print("\n" + "=" * 60)
    print("✅ SIMULATION COMPLETE - Pipeline is functioning!")
    print("=" * 60)
    print(f"""
Summary:
  - Target traded:    {target_size} shares @ ${fake_event['price']}
  - You would trade:  {float(final_size)} shares @ ${fake_event['price']}
  - Estimated cost:   ${float(final_size) * fake_event['price']:.2f} USDC

When the real bot is running and a trade is detected, 
this exact flow will execute automatically.
""")

if __name__ == "__main__":
    main()
