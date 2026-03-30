import time
import pandas as pd
import pandas_ta as ta
from hydra.data.models import Candle

_MIN_CANDLES = 210  # EMA_200 requires at least 200 candles; 210 gives buffer

# Common technical indicators used for trading signals.
# Uses ta.Study (the current pandas-ta API) instead of the deprecated
# ta.Strategy("All") which is not available in newer pandas-ta versions.
_DEFAULT_STUDY = ta.Study(
    name="hydra",
    ta=[
        {"kind": "rsi", "length": 14},
        {"kind": "ema", "length": 9},
        {"kind": "ema", "length": 20},
        {"kind": "ema", "length": 50},
        {"kind": "ema", "length": 200},
        {"kind": "sma", "length": 20},
        {"kind": "sma", "length": 50},
        {"kind": "macd"},
        {"kind": "bbands"},
        {"kind": "atr"},
        {"kind": "adx"},
        {"kind": "stoch"},
        {"kind": "stochrsi"},
        {"kind": "cci"},
        {"kind": "willr"},
        {"kind": "obv"},
        {"kind": "mfi"},
        {"kind": "mom"},
        {"kind": "roc"},
        {"kind": "tsi"},
        {"kind": "vwap"},
        {"kind": "supertrend"},
        {"kind": "kc"},
        {"kind": "donchian"},
        {"kind": "aroon"},
        {"kind": "ao"},
        {"kind": "er"},
    ],
)


class IndicatorCalculator:
    """Compute technical indicators for a candle list using pandas-ta."""

    def compute(self, candles: list[Candle]) -> dict:
        """
        Run a comprehensive set of pandas-ta indicators on candles.
        Returns {} if fewer than _MIN_CANDLES candles provided.
        NaN values are converted to None.
        """
        if len(candles) < _MIN_CANDLES:
            return {}

        df = pd.DataFrame([
            {
                "open": c.open, "high": c.high,
                "low": c.low, "close": c.close,
                "volume": c.volume,
            }
            for c in candles
        ])

        # cores=0 disables multiprocessing (avoids overhead for small DataFrames)
        df.ta.study(_DEFAULT_STUDY, cores=0)

        last = df.iloc[-1].to_dict()
        result: dict = {}
        for key, val in last.items():
            if key in ("open", "high", "low", "close", "volume"):
                continue
            if isinstance(val, float) and pd.isna(val):
                result[key] = None
            elif hasattr(val, "item"):          # numpy scalar → Python native
                result[key] = val.item()
            else:
                result[key] = val

        result["calculated_at"] = int(time.time() * 1000)
        return result
