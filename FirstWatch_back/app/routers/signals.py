import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Signal, User
from app.schemas import EvidenceOut, RefreshResult, SignalOut
from app.services.intelligence import refresh_signals_for_user

router = APIRouter(prefix="/api/signals", tags=["signals"])


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except ValueError:
        return None


def signal_out(row: Signal) -> SignalOut:
    try:
        entities = json.loads(row.affected_entities or "[]")
    except json.JSONDecodeError:
        entities = []
    try:
        raw_ev = json.loads(row.evidence_json or "[]")
    except json.JSONDecodeError:
        raw_ev = []
    evidence = []
    for e in raw_ev:
        published = e.get("published_at")
        if isinstance(published, str):
            published = _parse_dt(published)
        evidence.append(
            EvidenceOut(
                source=e.get("source") or "",
                url=e.get("url") or "",
                title=e.get("title") or "",
                published_at=published,
            )
        )
    return SignalOut(
        id=row.id,
        watch_type=row.watch_type,
        watch_id=row.watch_id,
        watch_label=row.watch_label,
        title=row.title,
        summary=row.summary,
        event_type=row.event_type,
        direction=row.direction,
        sentiment=row.sentiment,
        potential_impact=row.potential_impact,
        time_horizon=row.time_horizon,
        confidence=row.confidence,
        affected_entities=entities,
        evidence_count=row.evidence_count,
        evidence=evidence,
        first_evidence_at=row.first_evidence_at,
        latest_evidence_at=row.latest_evidence_at,
        market_already_moved=row.market_already_moved,
        signal_kind=row.signal_kind,
        source_agreement=row.source_agreement,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[SignalOut])
def list_signals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Signal)
        .filter(Signal.user_id == user.id)
        .order_by(Signal.updated_at.desc())
        .all()
    )
    return [signal_out(r) for r in rows]


@router.get("/{signal_id}", response_model=SignalOut)
def get_signal(signal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(Signal).filter(Signal.id == signal_id, Signal.user_id == user.id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal_out(row)


@router.post("/refresh", response_model=RefreshResult)
def refresh_signals(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = refresh_signals_for_user(db, user.id)
    return RefreshResult(ok=result["ok"], message=result["message"], details=result)
