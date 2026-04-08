from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Subject, UserSubject, User
from app.schemas import SubjectOut, UserSubjectOut, SubjectToggle
from app.auth import get_current_user

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


@router.get("/", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.get("/me", response_model=list[UserSubjectOut])
def get_my_subjects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_subjects = (
        db.query(UserSubject)
        .filter(UserSubject.user_id == user.id)
        .all()
    )
    return user_subjects


@router.post("/me/toggle", response_model=dict)
def toggle_subject(
    data: SubjectToggle,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    existing = (
        db.query(UserSubject)
        .filter(
            UserSubject.user_id == user.id,
            UserSubject.subject_id == data.subject_id,
        )
        .first()
    )

    if existing:
        db.delete(existing)
        db.commit()
        return {"action": "removed", "subject_id": data.subject_id}
    else:
        us = UserSubject(user_id=user.id, subject_id=data.subject_id)
        db.add(us)
        db.commit()
        return {"action": "added", "subject_id": data.subject_id}
