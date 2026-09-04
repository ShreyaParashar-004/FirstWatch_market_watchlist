from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.change_detection import detect_changes


def _obs(prices: list[float]):
    t0 = datetime(2026, 1, 1, 12, 0, 0)
    return [
        SimpleNamespace(price=p, observed_at=t0 + timedelta(minutes=i))
        for i, p in enumerate(prices)
    ]


def test_full_window_swing_net_zero():
    result = detect_changes(_obs([180, 175, 180]), threshold_pct=2.0)
    assert result is not None
    assert result.swing is True
    assert result.significant is True
    assert result.net_pct == 0.0
    assert result.range_pct > 2.0
    assert result.min_price == 175
    assert result.max_price == 180


def test_below_threshold_not_significant():
    result = detect_changes(_obs([100, 100.5]), threshold_pct=2.0)
    assert result is not None
    assert result.significant is False


def test_net_move_significant():
    result = detect_changes(_obs([100, 110]), threshold_pct=2.0)
    assert result.significant is True
    assert result.net_pct == 10.0
