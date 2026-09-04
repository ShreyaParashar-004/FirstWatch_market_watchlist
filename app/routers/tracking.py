from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import User, WatchlistCompany
from app.schemas import RefreshResult, TrackingResponse
from app.services.intelligence import refresh_market_for_user
from app.services.tracking import build_tracking_response, user_owns_ticker

router = APIRouter(prefix="/api/tracking", tags=["tracking"])


@router.get("", response_model=list[TrackingResponse])
def list_tracking(
    window_hours: int = Query(24, ge=1, le=24 * 30),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    companies = db.query(WatchlistCompany).filter(WatchlistCompany.user_id == user.id).all()
    return [build_tracking_response(db, c.ticker, window_hours) for c in companies]


@router.get("/{ticker}", response_model=TrackingResponse)
def get_tracking(
    ticker: str,
    window_hours: int = Query(24, ge=1, le=24 * 30),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user_owns_ticker(db, user.id, ticker):
        raise HTTPException(status_code=404, detail="Ticker is not on your watchlist")
    return build_tracking_response(db, ticker, window_hours)


@router.post("/refresh", response_model=RefreshResult)
def refresh_tracking(
    ticker: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = refresh_market_for_user(db, user.id, ticker)
    return RefreshResult(ok=result["ok"], message=result["message"], details=result)
