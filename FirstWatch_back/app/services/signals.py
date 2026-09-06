import json
import re
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import InformationItem, Notification, Signal, WatchlistCompany
from app.providers import AnalysisResult, InformationRecord
from app.providers.factory import get_ai_provider
from app.providers.market import utcnow
from app.services.confidence import agreement_from_directions, compute_confidence
from app.services.matching import Match
from app.services.normalize import content_hash
from app.services.tracking import build_tracking_response, user_owns_ticker

MAX_AI_EVIDENCE = 20
MAX_SIGNAL_EVIDENCE = 5


def _select_signal_evidence(records: list[InformationRecord]) -> list[InformationRecord]:
    """Keep recent, distinct records for AI and the public signal."""
    ranked = sorted(
        records,
        key=lambda record: record.published_at or datetime.min,
        reverse=True,
    )
    selected: list[InformationRecord] = []
    seen_titles: set[str] = set()
    for record in ranked:
        title_key = re.sub(r"[^a-z0-9]+", " ", record.title.lower()).strip()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        selected.append(record)
        if len(selected) == MAX_SIGNAL_EVIDENCE:
            break
    return selected


def persist_information(db: Session, records: list[InformationRecord]) -> list[InformationItem]:
    stored: list[InformationItem] = []
    for rec in records:
        existing = db.query(InformationItem).filter(InformationItem.canonical_id == rec.canonical_id).first()
        if existing:
            stored.append(existing)
            continue
        h = content_hash(rec.source, rec.title, rec.url)
        dup = db.query(InformationItem).filter(InformationItem.content_hash == h).first()
        if dup:
            stored.append(dup)
            continue
        row = InformationItem(
            canonical_id=rec.canonical_id,
            source=rec.source,
            url=rec.url,
            title=rec.title,
            content=rec.content,
            published_at=rec.published_at,
            retrieved_at=rec.retrieved_at or utcnow(),
            content_hash=h,
            is_primary=rec.is_primary,
            trusted=True,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        stored.append(row)
    return stored


def _evidence_payload(records: list[InformationRecord]) -> list[dict]:
    return [
        {
            "source": r.source,
            "url": r.url,
            "title": r.title,
            "content": r.content,
            "published_at": r.published_at,
        }
        for r in records
    ]


def _analyze(evidence: list[dict], context: dict) -> AnalysisResult:
    provider = get_ai_provider()
    try:
        return provider.analyze(evidence[:MAX_AI_EVIDENCE], context)
    except Exception:
        from app.providers.ai import fallback_analysis

        return fallback_analysis(evidence, context)


def _market_moved_for_watch(db: Session, user_id: int, watch_type: str, watch_label: str) -> bool:
    tickers: list[str] = []
    if watch_type == "company":
        tickers = [watch_label.upper()]
    else:
        tickers = [
            c.ticker
            for c in db.query(WatchlistCompany).filter(WatchlistCompany.user_id == user_id).all()
        ]
    window = get_settings().signal_lookback_hours
    for t in tickers:
        if watch_type == "company" and not user_owns_ticker(db, user_id, t):
            continue
        tracking = build_tracking_response(db, t, window_hours=window, provider_ok=True)
        if tracking.significant_movement:
            return True
    return False


def aggregate_signals(db: Session, user_id: int, matches: list[Match]) -> list[Signal]:
    groups: dict[tuple, list[Match]] = defaultdict(list)
    for m in matches:
        groups[(m.watch_type, m.watch_id, m.watch_label)].append(m)

    out: list[Signal] = []
    for (watch_type, watch_id, watch_label), items in groups.items():
        records = [m.record for m in items]
        unique_records = []
        seen = set()
        for r in records:
            if r.canonical_id in seen:
                continue
            seen.add(r.canonical_id)
            unique_records.append(r)
        persist_information(db, unique_records)
        signal_records = _select_signal_evidence(unique_records)
        evidence = _evidence_payload(signal_records)
        entities: list[str] = []
        for m in items:
            for e in m.entities:
                if e not in entities:
                    entities.append(e)
        analysis = _analyze(
            evidence,
            {"watch_type": watch_type, "watch_label": watch_label, "entities": entities, "theme": watch_label},
        )
        agreement = agreement_from_directions([analysis.impact_direction])
        if len(unique_records) > 1:
            agreement = agreement_from_directions([analysis.impact_direction] * len(unique_records))
        moved = _market_moved_for_watch(db, user_id, watch_type, watch_label)
        is_primary = any(r.is_primary for r in unique_records)
        confidence = compute_confidence(unique_records, agreement, moved, is_primary)
        kind = "confirmed" if moved else "early"
        if kind == "early":
            summary = (
                "Early signal — relevant information detected before significant market movement. "
                + analysis.reason
            )
            title = f"Early signal: {watch_label}"
        else:
            summary = (
                "Confirmed movement — market is already reacting. "
                "This does not establish causation unless evidence supports it. "
                + analysis.reason
            )
            title = f"Confirmed movement: {watch_label}"
        times = [r.published_at for r in signal_records if r.published_at]
        first_ts = min(times) if times else None
        last_ts = max(times) if times else None
        ev_public = [
            {
                "source": r.source,
                "url": r.url,
                "title": r.title,
                "published_at": r.published_at.isoformat() if r.published_at else None,
            }
            for r in signal_records
        ]
        existing = (
            db.query(Signal)
            .filter(
                Signal.user_id == user_id,
                Signal.watch_type == watch_type,
                Signal.watch_id == watch_id,
            )
            .order_by(Signal.updated_at.desc())
            .first()
        )
        now = utcnow()
        if existing:
            existing.title = title
            existing.summary = summary
            existing.event_type = analysis.event_type
            existing.direction = analysis.impact_direction
            existing.sentiment = analysis.sentiment
            existing.potential_impact = analysis.potential_impact
            existing.time_horizon = analysis.time_horizon
            existing.confidence = confidence
            existing.affected_entities = json.dumps(analysis.entities or entities)
            existing.evidence_count = len(signal_records)
            existing.evidence_json = json.dumps(ev_public, default=str)
            existing.first_evidence_at = first_ts
            existing.latest_evidence_at = last_ts
            existing.market_already_moved = moved
            existing.signal_kind = kind
            existing.source_agreement = agreement
            existing.updated_at = now
            db.commit()
            db.refresh(existing)
            out.append(existing)
        else:
            row = Signal(
                user_id=user_id,
                watch_type=watch_type,
                watch_id=watch_id,
                watch_label=watch_label,
                title=title,
                summary=summary,
                event_type=analysis.event_type,
                direction=analysis.impact_direction,
                sentiment=analysis.sentiment,
                potential_impact=analysis.potential_impact,
                time_horizon=analysis.time_horizon,
                confidence=confidence,
                affected_entities=json.dumps(analysis.entities or entities),
                evidence_count=len(signal_records),
                evidence_json=json.dumps(ev_public, default=str),
                first_evidence_at=first_ts,
                latest_evidence_at=last_ts,
                market_already_moved=moved,
                signal_kind=kind,
                source_agreement=agreement,
                created_at=now,
                updated_at=now,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            db.add(Notification(user_id=user_id, signal_id=row.id))
            db.commit()
            out.append(row)
    return out
