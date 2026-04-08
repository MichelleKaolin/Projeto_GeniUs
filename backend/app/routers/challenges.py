from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import (
    Challenge,
    ChallengeAttempt,
    Question,
    QuestionAnswer,
    User,
    UserSubject,
)
from app.schemas import ChallengeOut, AnswerSubmit, AnswerResult, AttemptResult
from app.auth import get_current_user

router = APIRouter(prefix="/api/challenges", tags=["Challenges"])


def _update_streak(user: User) -> None:
    today = date.today().isoformat()
    if user.last_activity_date == today:
        return

    yesterday = date.today().replace(day=date.today().day - 1).isoformat() if date.today().day > 1 else ""
    if user.last_activity_date == yesterday:
        user.streak_days += 1
    else:
        user.streak_days = 1

    if user.streak_days > user.streak_record:
        user.streak_record = user.streak_days
    user.last_activity_date = today


def _update_level(user: User) -> None:
    user.level = max(1, user.xp_total // 350 + 1)


@router.get("/", response_model=list[ChallengeOut])
def list_challenges(db: Session = Depends(get_db)):
    challenges = (
        db.query(Challenge)
        .options(joinedload(Challenge.subject), joinedload(Challenge.questions))
        .all()
    )
    return challenges


@router.get("/daily", response_model=ChallengeOut)
def get_daily_challenge(db: Session = Depends(get_db)):
    challenge = (
        db.query(Challenge)
        .options(joinedload(Challenge.subject), joinedload(Challenge.questions))
        .filter(Challenge.is_daily.is_(True))
        .first()
    )
    if not challenge:
        challenge = (
            db.query(Challenge)
            .options(joinedload(Challenge.subject), joinedload(Challenge.questions))
            .first()
        )
    if not challenge:
        raise HTTPException(status_code=404, detail="No challenges available")
    return challenge


@router.get("/{challenge_id}", response_model=ChallengeOut)
def get_challenge(challenge_id: int, db: Session = Depends(get_db)):
    challenge = (
        db.query(Challenge)
        .options(joinedload(Challenge.subject), joinedload(Challenge.questions))
        .filter(Challenge.id == challenge_id)
        .first()
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return challenge


@router.post("/{challenge_id}/start", response_model=AttemptResult)
def start_challenge(
    challenge_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")

    attempt = ChallengeAttempt(
        user_id=user.id,
        challenge_id=challenge_id,
        total_questions=challenge.question_count,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.post("/{challenge_id}/answer", response_model=AnswerResult)
def submit_answer(
    challenge_id: int,
    data: AnswerSubmit,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(ChallengeAttempt)
        .filter(
            ChallengeAttempt.user_id == user.id,
            ChallengeAttempt.challenge_id == challenge_id,
            ChallengeAttempt.is_completed.is_(False),
        )
        .order_by(ChallengeAttempt.started_at.desc())
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=400, detail="No active attempt found. Start the challenge first.")

    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = data.selected_answer == question.correct_answer_index
    xp_earned = question.xp_per_question if is_correct else 0

    answer = QuestionAnswer(
        attempt_id=attempt.id,
        question_id=data.question_id,
        selected_answer=data.selected_answer,
        is_correct=is_correct,
        time_taken_seconds=data.time_taken_seconds,
    )
    db.add(answer)

    if is_correct:
        attempt.correct_answers += 1
        attempt.xp_earned += xp_earned
        user.xp_total += xp_earned
        _update_level(user)

        # Update subject progress
        us = (
            db.query(UserSubject)
            .filter(
                UserSubject.user_id == user.id,
                UserSubject.subject_id == question.subject_id,
            )
            .first()
        )
        if us:
            us.correct_answers += 1
            us.questions_answered += 1
            us.progress_pct = min(100.0, us.correct_answers / max(us.questions_answered, 1) * 100)
        else:
            us = UserSubject(
                user_id=user.id,
                subject_id=question.subject_id,
                questions_answered=1,
                correct_answers=1,
                progress_pct=100.0,
            )
            db.add(us)
    else:
        us = (
            db.query(UserSubject)
            .filter(
                UserSubject.user_id == user.id,
                UserSubject.subject_id == question.subject_id,
            )
            .first()
        )
        if us:
            us.questions_answered += 1
            us.progress_pct = min(100.0, us.correct_answers / max(us.questions_answered, 1) * 100)

    attempt.score = attempt.correct_answers
    answers_count = (
        db.query(QuestionAnswer)
        .filter(QuestionAnswer.attempt_id == attempt.id)
        .count()
    )
    if answers_count >= attempt.total_questions:
        attempt.is_completed = True
        _update_streak(user)

    db.commit()

    return AnswerResult(
        is_correct=is_correct,
        correct_answer_index=question.correct_answer_index,
        xp_earned=xp_earned,
    )


@router.get("/{challenge_id}/results", response_model=AttemptResult)
def get_challenge_results(
    challenge_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(ChallengeAttempt)
        .filter(
            ChallengeAttempt.user_id == user.id,
            ChallengeAttempt.challenge_id == challenge_id,
        )
        .order_by(ChallengeAttempt.started_at.desc())
        .first()
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="No attempt found")
    return attempt
