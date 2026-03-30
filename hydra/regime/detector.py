# hydra/regime/detector.py
_VOLATILE_BBB_THRESHOLD = 0.08
_TRENDING_ADX_THRESHOLD = 25.0


class RegimeDetector:
    def detect(self, indicators: dict, close: float) -> str:
        bbb = indicators.get("BBB_5_2.0_2.0")
        adx = indicators.get("ADX_14")
        ema50 = indicators.get("EMA_50")

        if bbb is not None and bbb > _VOLATILE_BBB_THRESHOLD:
            return "volatile"
        if adx is not None and adx > _TRENDING_ADX_THRESHOLD:
            if ema50 is not None:
                return "trending_up" if close > ema50 else "trending_down"
        return "ranging"
