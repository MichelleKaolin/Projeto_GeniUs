from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, ChallengeAttempt, QuestionAnswer
from app.schemas import UserOut, UserUpdate, UserStats
from app.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])


def _get_ranking_position(db: Session, user_id: int) -> int:
    users_ranked = (
        db.query(User.id)
        .filter(User.is_active.is_(True))
        .order_by(User.xp_total.desc())
        .all()
    )
    for idx, (uid,) in enumerate(users_ranked, start=1):
        if uid == user_id:
            return idx
    return 0


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me", response_model=UserOut)
def update_user(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.name is not None:
        user.name = data.name
    if data.university is not None:
        user.university = data.university
    if data.course is not None:
        user.course = data.course
    db.commit()
    db.refresh(user)
    return user


@router.get("/me/stats", response_model=UserStats)
def get_my_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total_challenges = (
        db.query(func.count(ChallengeAttempt.id))
        .filter(
            ChallengeAttempt.user_id == user.id,
            ChallengeAttempt.is_completed.is_(True),
        )
        .scalar()
        or 0
    )

    total_answers = (
        db.query(func.count(QuestionAnswer.id))
        .join(ChallengeAttempt)
        .filter(ChallengeAttempt.user_id == user.id)
        .scalar()
        or 0
    )

    total_correct = (
        db.query(func.count(QuestionAnswer.id))
        .join(ChallengeAttempt)
        .filter(ChallengeAttempt.user_id == user.id, QuestionAnswer.is_correct.is_(True))
        .scalar()
        or 0
    )

    accuracy = (total_correct / total_answers * 100) if total_answers > 0 else 0.0
    ranking = _get_ranking_position(db, user.id)

    return UserStats(
        xp_total=user.xp_total,
        level=user.level,
        ranking_position=ranking,
        accuracy_pct=round(accuracy, 1),
        streak_days=user.streak_days,
        streak_record=user.streak_record,
        total_challenges=total_challenges,
        total_questions_answered=total_answers,
        total_correct=total_correct,
    )
