from dataclasses import dataclass

from app.models import MarketObservation


@dataclass
class ChangeResult:
    significant: bool
    swing: bool
    net_pct: float
    range_pct: float
    start_price: float
    end_price: float
    min_price: float
    max_price: float
    type: str


def detect_changes(observations: list[MarketObservation], threshold_pct: float) -> ChangeResult | None:
    """Inspect the FULL window. Net-zero paths can still be significant swings."""
    if len(observations) < 1:
        return None
    ordered = sorted(observations, key=lambda o: o.observed_at)
    prices = [o.price for o in ordered]
    start = prices[0]
    end = prices[-1]
    lo = min(prices)
    hi = max(prices)
    if start == 0:
        net_pct = 0.0
        range_pct = 0.0
    else:
        net_pct = ((end - start) / start) * 100.0
        range_pct = ((hi - lo) / start) * 100.0
    swing = False
    if len(prices) >= 3:
        hit_low = any(p == lo for p in prices[1:-1]) or lo not in (start, end)
        hit_high = any(p == hi for p in prices[1:-1]) or hi not in (start, end)
        reversed_path = (end - lo) > 0 and (hi - start) > 0 and lo < start
        reversed_up = (hi - start) > 0 and (hi - end) > 0
        swing = (hit_low or hit_high) and (reversed_path or reversed_up) and range_pct > 0
        if start == end and hi != lo:
            swing = True
    significant = range_pct >= threshold_pct or abs(net_pct) >= threshold_pct
    change_type = "swing" if swing else "net"
    return ChangeResult(
        significant=significant,
        swing=swing,
        net_pct=round(net_pct, 4),
        range_pct=round(range_pct, 4),
        start_price=start,
        end_price=end,
        min_price=lo,
        max_price=hi,
        type=change_type,
    )
