from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Achievement, UserAchievement, User
from app.schemas import AchievementOut, UserAchievementOut
from app.auth import get_current_user

router = APIRouter(prefix="/api/achievements", tags=["Achievements"])


@router.get("/", response_model=list[AchievementOut])
def list_achievements(db: Session = Depends(get_db)):
    return db.query(Achievement).all()


@router.get("/me", response_model=list[UserAchievementOut])
def get_my_achievements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_achievements = (
        db.query(UserAchievement)
        .options(joinedload(UserAchievement.achievement))
        .filter(UserAchievement.user_id == user.id)
        .all()
    )
    return user_achievements


@router.post("/check", response_model=list[AchievementOut])
def check_achievements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check and award any new achievements the user qualifies for."""
    from sqlalchemy import func
    from app.models import ChallengeAttempt, QuestionAnswer, CompetitionParticipant

    all_achievements = db.query(Achievement).all()
    earned_ids = {
        ua.achievement_id
        for ua in db.query(UserAchievement)
        .filter(UserAchievement.user_id == user.id)
        .all()
    }

    newly_earned = []

    for ach in all_achievements:
        if ach.id in earned_ids:
            continue

        qualified = False

        if ach.condition_type == "streak":
            qualified = user.streak_days >= ach.condition_value

        elif ach.condition_type == "challenges_completed":
            count = (
                db.query(func.count(ChallengeAttempt.id))
                .filter(
                    ChallengeAttempt.user_id == user.id,
                    ChallengeAttempt.is_completed.is_(True),
                )
                .scalar()
                or 0
            )
            qualified = count >= ach.condition_value

        elif ach.condition_type == "correct_answers":
            count = (
                db.query(func.count(QuestionAnswer.id))
                .join(ChallengeAttempt)
                .filter(
                    ChallengeAttempt.user_id == user.id,
                    QuestionAnswer.is_correct.is_(True),
                )
                .scalar()
                or 0
            )
            qualified = count >= ach.condition_value

        elif ach.condition_type == "level":
            qualified = user.level >= ach.condition_value

        elif ach.condition_type == "xp_total":
            qualified = user.xp_total >= ach.condition_value

        elif ach.condition_type == "competitions":
            count = (
                db.query(func.count(CompetitionParticipant.id))
                .filter(CompetitionParticipant.user_id == user.id)
                .scalar()
                or 0
            )
            qualified = count >= ach.condition_value

        if qualified:
            ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
            db.add(ua)
            newly_earned.append(ach)

    if newly_earned:
        db.commit()

    return newly_earned
