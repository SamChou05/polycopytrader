from decimal import Decimal, ROUND_DOWN

class RuleEngine:
    def __init__(self, config):
        self.config = config
        # Config should contain:
        # - mode: 'percentage', 'portfolio_scale', 'fixed_notional'
        # - percentage: float (e.g., 0.1 for 10%)
        # - fixed_amount: float (e.g., 10.0 USDC)
        # - min_size: float (e.g., 5.0 USDC or share count)

    def calculate_size(self, target_trade_size, target_portfolio_value=None, copier_portfolio_value=None, price=None):
        """
        Calculates the size of the trade to execute for the copier.
        Returns a Decimal representing the size.
        """
        mode = self.config.get('mode', 'percentage')
        
        if mode == 'percentage':
            return self._calculate_percentage_size(target_trade_size)
        elif mode == 'portfolio_scale':
            if target_portfolio_value is None or copier_portfolio_value is None:
                raise ValueError("Portfolio values required for scaling mode")
            return self._calculate_portfolio_scale_size(target_trade_size, target_portfolio_value, copier_portfolio_value)
        elif mode == 'fixed_notional':
            if price is None:
                raise ValueError("Price required for fixed notional mode")
            return self._calculate_fixed_notional_size(price)
        else:
            raise ValueError(f"Unknown sizing mode: {mode}")

    def _calculate_percentage_size(self, target_size):
        percentage = Decimal(str(self.config.get('percentage', 0.1)))
        target_size_dec = Decimal(str(target_size))
        return target_size_dec * percentage

    def _calculate_portfolio_scale_size(self, target_size, target_val, copier_val):
        target_val_dec = Decimal(str(target_val))
        copier_val_dec = Decimal(str(copier_val))
        target_size_dec = Decimal(str(target_size))
        
        if target_val_dec == 0:
            return Decimal('0')
            
        ratio = copier_val_dec / target_val_dec
        return target_size_dec * ratio

    def _calculate_fixed_notional_size(self, price):
        fixed_amount = Decimal(str(self.config.get('fixed_amount', 10.0)))
        price_dec = Decimal(str(price))
        
        if price_dec == 0:
            return Decimal('0')
            
        return fixed_amount / price_dec

    def apply_constraints(self, size, min_tick_size):
        """
        Rounds down to the nearest tick size and checks against minimum size.
        """
        min_tick = Decimal(str(min_tick_size))
        
        # Round down to nearest tick
        rounded_size = (size // min_tick) * min_tick
        
        # Check min size (assuming min_size in config is absolute min)
        min_allowed = Decimal(str(self.config.get('min_size', 0)))
        
        if rounded_size < min_allowed:
            return Decimal('0')
            
        return rounded_size
