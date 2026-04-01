import math
from datetime import datetime, timezone

LAMBDA_MAP = {
    "crypto": 0.029,      # ~24h half-life
    "us_stock": 0.012,    # ~58h half-life
    "kr_stock": 0.008,    # ~87h half-life
    "prediction": 0.023,  # ~30h half-life
}


def compute_decay_weight(
    publish_time: datetime,
    now: datetime,
    market: str,
) -> float:
    hours = (now - publish_time).total_seconds() / 3600
    if hours < 0:
        return 0.0
    lam = LAMBDA_MAP.get(market, 0.012)
    weight = math.exp(-lam * hours)
    return weight if weight >= 0.05 else 0.0


def aggregate_sentiment(items: list[dict], market: str) -> float:
    """
    Each item: {"score": float, "publish_time": datetime}
    Returns weighted sentiment in [-1.0, 1.0].
    """
    now = datetime.now(timezone.utc)
    total_weight = 0.0
    weighted_score = 0.0
    for item in items:
        w = compute_decay_weight(item["publish_time"], now, market)
        if w == 0.0:
            continue
        weighted_score += item["score"] * w
        total_weight += w
    if total_weight == 0.0:
        return 0.0
    return weighted_score / total_weight
