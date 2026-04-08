from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database import get_db
from app.models import (
    User,
    Challenge,
    ChallengeAttempt,
    QuestionAnswer,
    UserSubject,
    Subject,
    AntifraudEvent,
)
from app.schemas import (
    DashboardOverview,
    DashboardAnalytics,
    SubjectPerformance,
    DailyActivity,
    ChallengeOut,
)
from app.auth import get_current_user, get_optional_user

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


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


# ── API Endpoints ──


@router.get("/api/dashboard/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ranking = _get_ranking_position(db, user.id)

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

    # XP earned today
    from datetime import date

    today = date.today().isoformat()
    xp_today = (
        db.query(func.sum(ChallengeAttempt.xp_earned))
        .filter(
            ChallengeAttempt.user_id == user.id,
            func.date(ChallengeAttempt.started_at) == today,
        )
        .scalar()
        or 0
    )

    # Daily challenge
    daily = (
        db.query(Challenge)
        .options(joinedload(Challenge.subject), joinedload(Challenge.questions))
        .filter(Challenge.is_daily.is_(True))
        .first()
    )

    daily_out = None
    if daily:
        daily_out = ChallengeOut.model_validate(daily)

    return DashboardOverview(
        xp_total=user.xp_total,
        level=user.level,
        ranking_position=ranking,
        accuracy_pct=round(accuracy, 1),
        streak_days=user.streak_days,
        streak_record=user.streak_record,
        xp_today=xp_today,
        ranking_change=0,
        daily_challenge=daily_out,
    )


@router.get("/api/dashboard/analytics", response_model=DashboardAnalytics)
def get_dashboard_analytics(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Subject performance
    user_subjects = (
        db.query(UserSubject)
        .filter(UserSubject.user_id == user.id)
        .all()
    )

    subject_perf = []
    for us in user_subjects:
        subject = db.query(Subject).filter(Subject.id == us.subject_id).first()
        if subject:
            acc = (
                (us.correct_answers / us.questions_answered * 100)
                if us.questions_answered > 0
                else 0.0
            )
            subject_perf.append(
                SubjectPerformance(
                    subject_name=subject.name,
                    subject_icon=subject.icon,
                    progress_pct=round(us.progress_pct, 1),
                    questions_answered=us.questions_answered,
                    correct_answers=us.correct_answers,
                    accuracy_pct=round(acc, 1),
                )
            )

    # Daily activity (last 7 days)
    from datetime import date, timedelta

    daily_activity = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        d_str = d.isoformat()

        day_xp = (
            db.query(func.sum(ChallengeAttempt.xp_earned))
            .filter(
                ChallengeAttempt.user_id == user.id,
                func.date(ChallengeAttempt.started_at) == d_str,
            )
            .scalar()
            or 0
        )

        day_answers = (
            db.query(func.count(QuestionAnswer.id))
            .join(ChallengeAttempt)
            .filter(
                ChallengeAttempt.user_id == user.id,
                func.date(QuestionAnswer.answered_at) == d_str,
            )
            .scalar()
            or 0
        )

        day_correct = (
            db.query(func.count(QuestionAnswer.id))
            .join(ChallengeAttempt)
            .filter(
                ChallengeAttempt.user_id == user.id,
                func.date(QuestionAnswer.answered_at) == d_str,
                QuestionAnswer.is_correct.is_(True),
            )
            .scalar()
            or 0
        )

        daily_activity.append(
            DailyActivity(
                date=d_str,
                xp_earned=day_xp,
                questions_answered=day_answers,
                correct_answers=day_correct,
            )
        )

    # Total study time (from answer time_taken_seconds)
    total_time = (
        db.query(func.sum(QuestionAnswer.time_taken_seconds))
        .join(ChallengeAttempt)
        .filter(ChallengeAttempt.user_id == user.id)
        .scalar()
        or 0.0
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
    avg_accuracy = (total_correct / total_answers * 100) if total_answers > 0 else 0.0

    strongest = max(subject_perf, key=lambda x: x.accuracy_pct).subject_name if subject_perf else "N/A"
    weakest = min(subject_perf, key=lambda x: x.accuracy_pct).subject_name if subject_perf else "N/A"

    return DashboardAnalytics(
        subject_performance=subject_perf,
        daily_activity=daily_activity,
        total_study_time_minutes=round(total_time / 60, 1),
        avg_accuracy_pct=round(avg_accuracy, 1),
        strongest_subject=strongest,
        weakest_subject=weakest,
    )


# ── HTML Dashboard Views ──


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, db: Session = Depends(get_db)):
    users = (
        db.query(User)
        .filter(User.is_active.is_(True))
        .order_by(User.xp_total.desc())
        .all()
    )

    leaderboard = [
        {
            "rank": idx + 1,
            "name": u.name,
            "university": u.university,
            "course": u.course,
            "xp_total": u.xp_total,
            "level": u.level,
            "streak_days": u.streak_days,
            "initial": u.name[0].upper() if u.name else "?",
        }
        for idx, u in enumerate(users)
    ]

    # Subject stats
    subjects = db.query(Subject).all()
    subject_stats = []
    for s in subjects:
        total_q = (
            db.query(func.count(QuestionAnswer.id))
            .join(ChallengeAttempt)
            .join(Challenge)
            .filter(Challenge.subject_id == s.id)
            .scalar()
            or 0
        )
        correct_q = (
            db.query(func.count(QuestionAnswer.id))
            .join(ChallengeAttempt)
            .join(Challenge)
            .filter(Challenge.subject_id == s.id, QuestionAnswer.is_correct.is_(True))
            .scalar()
            or 0
        )
        subject_stats.append(
            {
                "name": s.name,
                "icon": s.icon,
                "total_questions": total_q,
                "correct_answers": correct_q,
                "accuracy": round(correct_q / total_q * 100, 1) if total_q > 0 else 0,
            }
        )

    # General stats
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_challenges_completed = (
        db.query(func.count(ChallengeAttempt.id))
        .filter(ChallengeAttempt.is_completed.is_(True))
        .scalar()
        or 0
    )
    total_questions_answered = db.query(func.count(QuestionAnswer.id)).scalar() or 0
    total_fraud_events = db.query(func.count(AntifraudEvent.id)).scalar() or 0

    # Fraud breakdown
    fraud_breakdown = (
        db.query(
            AntifraudEvent.event_type,
            func.count(AntifraudEvent.id).label("count"),
        )
        .group_by(AntifraudEvent.event_type)
        .all()
    )
    fraud_data = {e.event_type: e.count for e in fraud_breakdown}

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "leaderboard": leaderboard,
            "subject_stats": subject_stats,
            "total_users": total_users,
            "total_challenges_completed": total_challenges_completed,
            "total_questions_answered": total_questions_answered,
            "total_fraud_events": total_fraud_events,
            "fraud_data": fraud_data,
        },
    )


@router.get("/dashboard/student/{user_id}", response_class=HTMLResponse)
def student_detail_page(user_id: int, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return HTMLResponse("<h1>Student not found</h1>", status_code=404)

    ranking = _get_ranking_position(db, user.id)

    # Subject performance
    user_subjects = db.query(UserSubject).filter(UserSubject.user_id == user.id).all()
    subjects_data = []
    for us in user_subjects:
        subject = db.query(Subject).filter(Subject.id == us.subject_id).first()
        if subject:
            acc = (
                round(us.correct_answers / us.questions_answered * 100, 1)
                if us.questions_answered > 0
                else 0
            )
            subjects_data.append(
                {
                    "name": subject.name,
                    "icon": subject.icon,
                    "progress": round(us.progress_pct, 1),
                    "questions": us.questions_answered,
                    "correct": us.correct_answers,
                    "accuracy": acc,
                }
            )

    # Recent attempts
    attempts = (
        db.query(ChallengeAttempt)
        .filter(ChallengeAttempt.user_id == user.id)
        .order_by(ChallengeAttempt.started_at.desc())
        .limit(10)
        .all()
    )
    attempts_data = []
    for a in attempts:
        challenge = db.query(Challenge).filter(Challenge.id == a.challenge_id).first()
        attempts_data.append(
            {
                "challenge_title": challenge.title if challenge else "Unknown",
                "score": a.correct_answers,
                "total": a.total_questions,
                "xp_earned": a.xp_earned,
                "completed": a.is_completed,
                "date": a.started_at.strftime("%Y-%m-%d %H:%M") if a.started_at else "",
            }
        )

    # Fraud events
    fraud_events = (
        db.query(AntifraudEvent)
        .filter(AntifraudEvent.user_id == user.id)
        .order_by(AntifraudEvent.created_at.desc())
        .limit(20)
        .all()
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
    accuracy = round(total_correct / total_answers * 100, 1) if total_answers > 0 else 0

    return templates.TemplateResponse(
        request=request,
        name="student_detail.html",
        context={
            "user": user,
            "ranking": ranking,
            "accuracy": accuracy,
            "total_answers": total_answers,
            "total_correct": total_correct,
            "subjects_data": subjects_data,
            "attempts_data": attempts_data,
            "fraud_events": fraud_events,
        },
    )
