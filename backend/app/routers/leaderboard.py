from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LeaderboardEntry

router = APIRouter(prefix="/api/leaderboard", tags=["Leaderboard"])


@router.get("/", response_model=list[LeaderboardEntry])
def get_leaderboard(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    users = (
        db.query(User)
        .filter(User.is_active.is_(True))
        .order_by(User.xp_total.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        LeaderboardEntry(
            rank=offset + idx + 1,
            user_id=u.id,
            name=u.name,
            university=u.university,
            xp_total=u.xp_total,
            level=u.level,
            avatar_initial=u.name[0].upper() if u.name else "?",
        )
        for idx, u in enumerate(users)
    ]


@router.get("/subject/{subject_id}", response_model=list[LeaderboardEntry])
def get_subject_leaderboard(
    subject_id: int,
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    from app.models import UserSubject

    user_subjects = (
        db.query(UserSubject)
        .filter(UserSubject.subject_id == subject_id)
        .order_by(UserSubject.correct_answers.desc())
        .limit(limit)
        .all()
    )

    entries = []
    for idx, us in enumerate(user_subjects):
        user = db.query(User).filter(User.id == us.user_id).first()
        if user:
            entries.append(
                LeaderboardEntry(
                    rank=idx + 1,
                    user_id=user.id,
                    name=user.name,
                    university=user.university,
                    xp_total=user.xp_total,
                    level=user.level,
                    avatar_initial=user.name[0].upper() if user.name else "?",
                )
            )
    return entries
