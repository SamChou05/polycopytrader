import pytest
from decimal import Decimal
from rule_engine import RuleEngine

def test_percentage_sizing():
    config = {'mode': 'percentage', 'percentage': 0.1}
    engine = RuleEngine(config)
    
    # Target trades 100, copier should trade 10
    size = engine.calculate_size(100)
    assert size == Decimal('10.0')

def test_portfolio_scaling():
    config = {'mode': 'portfolio_scale'}
    engine = RuleEngine(config)
    
    # Target: 1000 val, trades 100 (10%)
    # Copier: 100 val, should trade 10 (10%)
    size = engine.calculate_size(100, target_portfolio_value=1000, copier_portfolio_value=100)
    assert size == Decimal('10.0')

def test_fixed_notional():
    config = {'mode': 'fixed_notional', 'fixed_amount': 50.0}
    engine = RuleEngine(config)
    
    # Price 0.5, should buy 100 shares
    size = engine.calculate_size(None, price=0.5)
    assert size == Decimal('100.0')

def test_min_size_constraint():
    config = {'mode': 'percentage', 'percentage': 0.01, 'min_size': 5.0}
    engine = RuleEngine(config)
    
    # Target 100 -> Copier 1.0. Below min 5.0
    size = engine.calculate_size(100)
    final_size = engine.apply_constraints(size, min_tick_size=0.1)
    assert final_size == Decimal('0')

def test_rounding():
    config = {'mode': 'percentage', 'percentage': 1.0}
    engine = RuleEngine(config)
    
    # Size 10.123, tick 0.1 -> 10.1
    size = Decimal('10.123')
    final_size = engine.apply_constraints(size, min_tick_size=0.1)
    assert final_size == Decimal('10.1')
