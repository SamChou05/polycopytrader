import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from monitor import Monitor
from rule_engine import RuleEngine
from executor import Executor
from main import main # We might need to refactor main to be more testable or just test the flow manually here

# We'll test the interaction between components directly
def test_full_flow_integration():
    # 1. Setup Mocks
    mock_clob_client = MagicMock()
    
    # 2. Initialize Components
    # Rule Engine: 10% copy size
    rule_config = {'mode': 'percentage', 'percentage': 0.1, 'min_size': 1.0}
    rule_engine = RuleEngine(rule_config)
    
    # Executor: Mock the internal client
    # Patch PRIVATE_KEY to avoid ValueError during init
    with patch('executor.PRIVATE_KEY', '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'):
        executor = Executor(dry_run=False)
    
    executor.client = mock_clob_client
    executor.client = mock_clob_client
    # Mock create_and_post_order response
    mock_clob_client.create_and_post_order.return_value = {'orderID': '0x123', 'status': 'success'}
    
    # 3. Simulate Trade Event
    # Target buys 100 shares of Asset A at $0.50
    trade_event = {
        'asset': '0xAssetA',
        'side': 'BUY',
        'size': 100.0,
        'price': 0.50,
        'timestamp': 1234567890
    }
    
    # 4. Define the callback that Main would use
    def on_trade_detected(trade):
        # This logic mirrors the callback in main.py
        target_size = trade.get('size')
        copier_size = rule_engine.calculate_size(target_size)
        final_size = rule_engine.apply_constraints(copier_size, min_tick_size=0.01)
        
        if final_size > 0:
            token_id = trade.get('asset')
            side = trade.get('side')
            price = trade.get('price')
            executor.place_order(token_id, side, price, float(final_size))

    # 5. Trigger the callback (Simulating Monitor calling it)
    on_trade_detected(trade_event)
    
    # 6. Verify Executor called ClobClient correctly
    # Expected size: 100 * 0.1 = 10.0
    mock_clob_client.create_and_post_order.assert_called_once()
    
    args, _ = mock_clob_client.create_and_post_order.call_args
    order_args = args[0]
    
    assert order_args.token_id == '0xAssetA'
    assert order_args.side == 'BUY'
    assert order_args.price == 0.50
    assert order_args.size == 10.0

def test_monitor_parsing_integration():
    # Test that Monitor correctly parses a raw message and calls callback
    # We need to mock websocket and requests
    
    callback = MagicMock()
    monitor = Monitor("0xTarget", callback)  # Updated to use positional args
    
    # Simulate a raw RTDS event
    # Note: This structure depends on actual RTDS payload. 
    # Based on PRD: "orders_matched event within the activity topic"
    raw_event = {
        'maker': '0xTarget',  # Target is maker
        'taker': '0xOther',
        'asset': '0xAssetB',
        'side': 'SELL',  # Maker is selling
        'size': 500.0,
        'price': 0.75,
        'timestamp': 1234567890
    }
    
    # Inject event directly into _process_event to test filtering logic
    monitor._process_event(raw_event, source="test")
    
    callback.assert_called_once()
    trade = callback.call_args[0][0]
    
    assert trade['asset'] == '0xAssetB'
    assert trade['size'] == 500.0
    assert trade['side'] == 'SELL'
    assert trade['wallet_address'] == '0xtarget'  # Normalized to lowercase


