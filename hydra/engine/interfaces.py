from dataclasses import dataclass


@dataclass
class RegimeProbabilities:
    bull: float
    neutral: float
    bear: float

    def __post_init__(self):
        total = self.bull + self.neutral + self.bear
        assert abs(total - 1.0) < 0.01, f"Regime probs must sum to 1.0, got {total}"


@dataclass
class SizingParams:
    base_size: float
    bear_risk_factor: float = 1.5
    bull_bonus_factor: float = 0.3
    min_position: float = 0.0
    max_position: float = 1.0


def compute_regime_adjusted_size(
    regime: RegimeProbabilities,
    params: SizingParams,
) -> float:
    size = params.base_size
    size *= (1 - regime.bear * params.bear_risk_factor)
    size *= (1 + regime.bull * params.bull_bonus_factor)
    return max(params.min_position, min(params.max_position, size))


# Rule-based regime → RegimeProbabilities mapping.
# Replaced by HMM output when ML module #1 is available.
_REGIME_PROB_MAP: dict[str, RegimeProbabilities] = {
    "trending_up":   RegimeProbabilities(bull=0.70, neutral=0.20, bear=0.10),
    "trending_down": RegimeProbabilities(bull=0.10, neutral=0.20, bear=0.70),
    "volatile":      RegimeProbabilities(bull=0.15, neutral=0.25, bear=0.60),
    "ranging":       RegimeProbabilities(bull=0.25, neutral=0.50, bear=0.25),
}


def regime_str_to_probabilities(regime: str) -> RegimeProbabilities:
    """Convert rule-based regime label to RegimeProbabilities.

    Acts as a shim until HMM (#1) provides native probability output.
    """
    return _REGIME_PROB_MAP.get(regime, _REGIME_PROB_MAP["ranging"])
