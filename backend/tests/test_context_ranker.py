import math
from datetime import datetime, timedelta, timezone

import pytest

from ..context.ranker import final_score, recency_score

_NOW = datetime.now(timezone.utc)


def _ago(days: float) -> datetime:
    return _NOW - timedelta(days=days)


def test_recency_score_fresh():
    score = recency_score(_ago(0))
    assert score > 0.99


def test_recency_score_half_life():
    score = recency_score(_ago(30))
    assert 0.48 < score < 0.52  # should be ~0.5 at 30-day half-life


def test_recency_score_old():
    score = recency_score(_ago(90))
    assert score < 0.15  # 3 half-lives → ~0.125


def test_recency_score_none():
    assert recency_score(None) == 0.0


def test_recency_score_naive_datetime():
    naive = datetime.utcnow() - timedelta(days=1)
    score = recency_score(naive)
    assert 0.0 < score < 1.0


def test_recency_score_no_future_overflow():
    future = _ago(-1)  # 1 day in the future
    score = recency_score(future)
    assert score <= 1.0


def test_final_score_pure_relevance():
    score = final_score(relevance=0.8, recency=0.2, recency_weight=0.0)
    assert score == pytest.approx(0.8)


def test_final_score_pure_recency():
    score = final_score(relevance=0.8, recency=0.2, recency_weight=1.0)
    assert score == pytest.approx(0.2)


def test_final_score_balanced():
    score = final_score(relevance=1.0, recency=0.0, recency_weight=0.5)
    assert score == pytest.approx(0.5)


def test_final_score_weighted():
    score = final_score(relevance=0.6, recency=0.4, recency_weight=0.3)
    expected = 0.7 * 0.6 + 0.3 * 0.4
    assert score == pytest.approx(expected)
