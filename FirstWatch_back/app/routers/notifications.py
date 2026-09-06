from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Notification, User
from app.schemas import NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


def notification_out(row: Notification) -> NotificationOut:
    return NotificationOut(
        id=row.id,
        signal_id=row.signal_id,
        title=row.signal.title,
        watch_label=row.signal.watch_label,
        created_at=row.created_at,
        read_at=row.read_at,
    )


@router.get("", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return [notification_out(row) for row in rows]


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    if row.read_at is None:
        row.read_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
    return notification_out(row)
