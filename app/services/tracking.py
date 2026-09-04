from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import MarketObservation, WatchlistCompany
from app.providers.market import utcnow
from app.schemas import ChangeDetail, ObservationOut, TrackingResponse
from app.services.change_detection import detect_changes


def _status(latest: MarketObservation | None, provider_ok: bool, stale_after: int) -> str:
    if latest is None:
        return "no_data"
    age = (utcnow() - latest.retrieved_at).total_seconds()
    if not provider_ok or age > stale_after:
        return "stale"
    return "ok"


def list_window(db: Session, ticker: str, window_hours: int) -> list[MarketObservation]:
    start = utcnow() - timedelta(hours=window_hours)
    return (
        db.query(MarketObservation)
        .filter(MarketObservation.ticker == ticker.upper(), MarketObservation.observed_at >= start)
        .order_by(MarketObservation.observed_at.asc())
        .all()
    )


def latest_observation(db: Session, ticker: str) -> MarketObservation | None:
    return (
        db.query(MarketObservation)
        .filter(MarketObservation.ticker == ticker.upper())
        .order_by(MarketObservation.observed_at.desc(), MarketObservation.id.desc())
        .first()
    )


def store_observation(db: Session, ticker: str, price: float, currency: str, observed_at: datetime, source: str) -> MarketObservation:
    row = MarketObservation(
        ticker=ticker.upper(),
        price=price,
        currency=currency,
        observed_at=observed_at,
        retrieved_at=utcnow(),
        source=source,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def build_tracking_response(
    db: Session,
    ticker: str,
    window_hours: int,
    provider_ok: bool = True,
) -> TrackingResponse:
    settings = get_settings()
    key = ticker.upper()
    rows = list_window(db, key, window_hours)
    latest = rows[-1] if rows else latest_observation(db, key)
    status = _status(latest, provider_ok, settings.stale_after_seconds)
    if latest is None:
        return TrackingResponse(
            ticker=key,
            status="no_data",
            window_hours=window_hours,
            message="No stored observations for this ticker.",
        )
    change = detect_changes(rows, settings.change_threshold_pct) if rows else None
    change_out = None
    significant = False
    if change:
        significant = change.significant
        change_out = ChangeDetail(
            type=change.type,
            start_price=change.start_price,
            end_price=change.end_price,
            min_price=change.min_price,
            max_price=change.max_price,
            net_pct=change.net_pct,
            range_pct=change.range_pct,
            swing=change.swing,
            significant=change.significant,
        )
    obs_out = [
        ObservationOut(
            ticker=r.ticker,
            price=r.price,
            currency=r.currency,
            observed_at=r.observed_at,
            retrieved_at=r.retrieved_at,
            source=r.source,
        )
        for r in rows
    ]
    message = None
    if status == "stale":
        message = "Market provider unavailable or data is stale. Returning stored observations."
    return TrackingResponse(
        ticker=key,
        status=status,
        latest_price=latest.price,
        currency=latest.currency,
        latest_observed_at=latest.observed_at,
        window_hours=window_hours,
        significant_movement=significant,
        change=change_out,
        observations=obs_out,
        message=message,
    )


def user_owns_ticker(db: Session, user_id: int, ticker: str) -> WatchlistCompany | None:
    return (
        db.query(WatchlistCompany)
        .filter(WatchlistCompany.user_id == user_id, WatchlistCompany.ticker == ticker.upper())
        .first()
    )
