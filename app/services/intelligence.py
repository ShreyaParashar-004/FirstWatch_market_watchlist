from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import InformationItem, WatchlistCompany, WatchlistTheme
from app.providers import InformationRecord
from app.providers.factory import get_information_provider, get_market_provider
from app.providers.market import utcnow
from app.services.matching import match_records
from app.services.normalize import deduplicate
from app.services.signals import aggregate_signals
from app.services.tracking import store_observation, user_owns_ticker


def refresh_market_for_user(db: Session, user_id: int, ticker: str | None = None) -> dict:
    provider = get_market_provider()
    companies = db.query(WatchlistCompany).filter(WatchlistCompany.user_id == user_id).all()
    targets = [c.ticker for c in companies]
    if ticker:
        if not user_owns_ticker(db, user_id, ticker):
            return {"ok": False, "message": "Ticker is not on your watchlist.", "stored": 0, "failed": []}
        targets = [ticker.upper()]
    stored = 0
    failed: list[str] = []
    for t in targets:
        try:
            quote = provider.get_quote(t)
            store_observation(db, quote.ticker, quote.price, quote.currency, quote.observed_at, quote.source)
            stored += 1
        except Exception:
            failed.append(t)
    ok = stored > 0 or not targets
    msg = "Market observations stored." if stored else "Market provider unavailable."
    if failed and stored:
        msg = "Partial market refresh; some tickers used stale data on next read."
    return {"ok": ok, "message": msg, "stored": stored, "failed": failed}


def _hints(companies: list[WatchlistCompany], themes: list[WatchlistTheme]) -> list[str]:
    hints: list[str] = []
    for c in companies:
        hints.append(c.ticker)
        if c.name:
            hints.append(c.name)
    for t in themes:
        hints.append(t.name)
        hints.extend([k.strip() for k in (t.keywords or "").split(",") if k.strip()])
    return hints


def _cached_information(db: Session) -> list[InformationRecord]:
    cutoff = utcnow() - timedelta(hours=get_settings().information_cache_hours)
    rows = db.query(InformationItem).filter(InformationItem.retrieved_at >= cutoff).all()
    return [
        InformationRecord(
            canonical_id=r.canonical_id,
            source=r.source,
            url=r.url,
            title=r.title,
            content=r.content,
            published_at=r.published_at,
            retrieved_at=r.retrieved_at,
            is_primary=r.is_primary,
        )
        for r in rows
    ]


def refresh_signals_for_user(db: Session, user_id: int) -> dict:
    companies = db.query(WatchlistCompany).filter(WatchlistCompany.user_id == user_id).all()
    themes = db.query(WatchlistTheme).filter(WatchlistTheme.user_id == user_id).all()
    if not companies and not themes:
        return {"ok": True, "message": "Watchlist empty.", "signals": 0, "intelligence": "idle"}
    hints = _hints(companies, themes)
    provider = get_information_provider()
    intel_status = "ok"
    try:
        raw = provider.fetch(hints)
        records = deduplicate(raw)
    except Exception:
        records = deduplicate(_cached_information(db))
        intel_status = "cached" if records else "unavailable"
    if intel_status == "unavailable":
        return {
            "ok": False,
            "message": "Intelligence unavailable. No cached information.",
            "signals": 0,
            "intelligence": intel_status,
        }
    matches = match_records(records, companies, themes)
    if not matches:
        return {
            "ok": True,
            "message": "No watchlist matches in retrieved information.",
            "signals": 0,
            "intelligence": intel_status,
        }
    signals = aggregate_signals(db, user_id, matches)
    return {
        "ok": True,
        "message": "Signals updated.",
        "signals": len(signals),
        "intelligence": intel_status,
    }
