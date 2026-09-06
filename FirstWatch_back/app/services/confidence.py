from datetime import datetime
from statistics import mean

from app.providers import InformationRecord
from app.providers.market import utcnow

SOURCE_RELIABILITY = {
    "reuters": 0.95,
    "ap": 0.95,
    "bbc": 0.9,
    "ft": 0.9,
    "bloomberg": 0.9,
    "wsj": 0.9,
    "cnbc": 0.8,
    "sec": 0.98,
    "yahoo": 0.5,
    "mock": 0.7,
}


def source_score(name: str) -> float:
    key = (name or "").strip().lower()
    for prefix, score in SOURCE_RELIABILITY.items():
        if prefix in key:
            return score
    return 0.55


def recency_score(published_at: datetime | None) -> float:
    if published_at is None:
        return 0.4
    hours = max(0.0, (utcnow() - published_at).total_seconds() / 3600.0)
    return max(0.0, 1.0 - (hours / 72.0))


def agreement_from_directions(directions: list[str]) -> str:
    cleaned = [d for d in directions if d and d != "uncertain"]
    if len(cleaned) == 0:
        return "uncertain"
    if len(set(cleaned)) == 1:
        return "agree"
    if "mixed" in cleaned or len(set(cleaned)) > 1:
        return "mixed"
    return "uncertain"


def compute_confidence(
    records: list[InformationRecord],
    agreement: str,
    market_moved: bool,
    is_primary: bool,
) -> float:
    if not records:
        return 0.05
    reliability = mean(source_score(r.source) for r in records)
    recency = max(recency_score(r.published_at) for r in records)
    n_sources = len({r.source.lower() for r in records})
    source_count = min(1.0, n_sources / 3.0)
    agreement_score = {"agree": 1.0, "mixed": 0.5, "uncertain": 0.4}.get(agreement, 0.4)
    primary = 1.0 if is_primary else 0.6
    moved = 0.85 if market_moved else 0.75
    conf = (
        0.25 * reliability
        + 0.20 * recency
        + 0.20 * source_count
        + 0.15 * agreement_score
        + 0.10 * primary
        + 0.10 * moved
    )
    return round(min(0.95, max(0.05, conf)), 3)
