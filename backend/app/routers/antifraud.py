from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AntifraudEvent, User
from app.schemas import AntifraudReport, AntifraudEventOut
from app.auth import get_current_user

router = APIRouter(prefix="/api/antifraud", tags=["Anti-Fraud"])

PENALTY_MAP = {
    "copy_paste": 50,
    "tab_switch": 30,
    "screen_change": 40,
    "suspicious_speed": 60,
}


@router.post("/report", response_model=AntifraudEventOut)
def report_fraud_event(
    data: AntifraudReport,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    penalty = PENALTY_MAP.get(data.event_type, 20)

    event = AntifraudEvent(
        user_id=user.id,
        attempt_id=data.attempt_id,
        event_type=data.event_type,
        details=data.details,
        penalty_xp=penalty,
    )
    db.add(event)

    user.xp_total = max(0, user.xp_total - penalty)
    db.commit()
    db.refresh(event)

    return event


@router.get("/events", response_model=list[AntifraudEventOut])
def get_my_fraud_events(
    limit: int = Query(default=50, le=200),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    events = (
        db.query(AntifraudEvent)
        .filter(AntifraudEvent.user_id == user.id)
        .order_by(AntifraudEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return events


@router.get("/events/{user_id}", response_model=list[AntifraudEventOut])
def get_user_fraud_events(
    user_id: int,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    events = (
        db.query(AntifraudEvent)
        .filter(AntifraudEvent.user_id == user_id)
        .order_by(AntifraudEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return events


@router.get("/summary", response_model=dict)
def get_antifraud_summary(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from sqlalchemy import func

    events = (
        db.query(
            AntifraudEvent.event_type,
            func.count(AntifraudEvent.id).label("count"),
            func.sum(AntifraudEvent.penalty_xp).label("total_penalty"),
        )
        .filter(AntifraudEvent.user_id == user.id)
        .group_by(AntifraudEvent.event_type)
        .all()
    )

    summary = {
        "total_events": sum(e.count for e in events),
        "total_penalty_xp": sum(e.total_penalty or 0 for e in events),
        "by_type": {
            e.event_type: {"count": e.count, "penalty_xp": e.total_penalty or 0}
            for e in events
        },
    }
    return summary
