from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Competition, CompetitionParticipant, User
from app.schemas import (
    CompetitionCreate,
    CompetitionOut,
    CompetitionParticipantOut,
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/competitions", tags=["Competitions"])


@router.post("/", response_model=CompetitionOut, status_code=201)
def create_competition(
    data: CompetitionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comp = Competition(
        creator_id=user.id,
        title=data.title,
        comp_type=data.comp_type,
        subject_id=data.subject_id,
        max_participants=data.max_participants,
        question_count=data.question_count,
        time_limit_seconds=data.time_limit_seconds,
    )
    db.add(comp)
    db.flush()

    participant = CompetitionParticipant(
        competition_id=comp.id,
        user_id=user.id,
    )
    db.add(participant)
    db.commit()
    db.refresh(comp)

    return CompetitionOut(
        id=comp.id,
        title=comp.title,
        comp_type=comp.comp_type,
        status=comp.status,
        max_participants=comp.max_participants,
        question_count=comp.question_count,
        time_limit_seconds=comp.time_limit_seconds,
        created_at=comp.created_at,
        participant_count=1,
    )


@router.get("/", response_model=list[CompetitionOut])
def list_competitions(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Competition)
    if status_filter:
        query = query.filter(Competition.status == status_filter)
    competitions = query.order_by(Competition.created_at.desc()).limit(limit).all()

    results = []
    for comp in competitions:
        count = (
            db.query(CompetitionParticipant)
            .filter(CompetitionParticipant.competition_id == comp.id)
            .count()
        )
        results.append(
            CompetitionOut(
                id=comp.id,
                title=comp.title,
                comp_type=comp.comp_type,
                status=comp.status,
                max_participants=comp.max_participants,
                question_count=comp.question_count,
                time_limit_seconds=comp.time_limit_seconds,
                created_at=comp.created_at,
                participant_count=count,
            )
        )
    return results


@router.post("/{competition_id}/join", response_model=dict)
def join_competition(
    competition_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comp = db.query(Competition).filter(Competition.id == competition_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")

    if comp.status != "waiting":
        raise HTTPException(status_code=400, detail="Competition is not accepting participants")

    existing = (
        db.query(CompetitionParticipant)
        .filter(
            CompetitionParticipant.competition_id == competition_id,
            CompetitionParticipant.user_id == user.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already joined this competition")

    count = (
        db.query(CompetitionParticipant)
        .filter(CompetitionParticipant.competition_id == competition_id)
        .count()
    )
    if count >= comp.max_participants:
        raise HTTPException(status_code=400, detail="Competition is full")

    participant = CompetitionParticipant(
        competition_id=competition_id,
        user_id=user.id,
    )
    db.add(participant)
    db.commit()

    return {"message": "Joined competition successfully", "competition_id": competition_id}


@router.post("/{competition_id}/start", response_model=dict)
def start_competition(
    competition_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comp = db.query(Competition).filter(Competition.id == competition_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")

    if comp.creator_id != user.id:
        raise HTTPException(status_code=403, detail="Only the creator can start the competition")

    if comp.status != "waiting":
        raise HTTPException(status_code=400, detail="Competition already started or ended")

    comp.status = "active"
    comp.started_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Competition started", "competition_id": competition_id}


@router.get("/{competition_id}/results", response_model=list[CompetitionParticipantOut])
def get_competition_results(
    competition_id: int,
    db: Session = Depends(get_db),
):
    participants = (
        db.query(CompetitionParticipant)
        .filter(CompetitionParticipant.competition_id == competition_id)
        .order_by(CompetitionParticipant.score.desc())
        .all()
    )

    results = []
    for idx, p in enumerate(participants):
        user = db.query(User).filter(User.id == p.user_id).first()
        results.append(
            CompetitionParticipantOut(
                user_id=p.user_id,
                name=user.name if user else "Unknown",
                score=p.score,
                rank=idx + 1,
            )
        )
    return results
