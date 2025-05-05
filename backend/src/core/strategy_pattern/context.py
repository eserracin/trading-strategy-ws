# src/core/strategy_pattern/context.py
from src.strategies.scalping.scalping_lp import ScalpingStrategyLP

class ContextStrategy:
    STRATEGIES = {
        "scalping-lp": ScalpingStrategyLP
    }


    @classmethod
    def get_strategy(cls, strategy, **kwargs):
        strategy_class = cls.STRATEGIES.get(strategy.lower())
        if strategy_class is None:
            raise ValueError(f"Strategy {strategy} not found")
        return strategy_class(**kwargs)