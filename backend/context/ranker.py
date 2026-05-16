import math
from datetime import datetime, timezone

_HALF_LIFE_DAYS = 30.0
_DECAY_K = math.log(2) / _HALF_LIFE_DAYS


def recency_score(updated_at: datetime | None) -> float:
    """Exponential decay: 1.0 = just updated, approaches 0 as age grows.
    Half-life is 30 days — a document untouched for 30 days scores ~0.5."""
    if updated_at is None:
        return 0.0
    now = datetime.now(timezone.utc)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - updated_at).total_seconds() / 86_400)
    return math.exp(-_DECAY_K * age_days)


def final_score(relevance: float, recency: float, recency_weight: float) -> float:
    """Weighted blend: relevance_weight * relevance + recency_weight * recency."""
    return (1.0 - recency_weight) * relevance + recency_weight * recency
