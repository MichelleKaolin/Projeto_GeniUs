from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    university = Column(String(255), default="")
    course = Column(String(255), default="")
    xp_total = Column(Integer, default=0)
    level = Column(Integer, default=1)
    streak_days = Column(Integer, default=0)
    streak_record = Column(Integer, default=0)
    last_activity_date = Column(String(10), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    subjects = relationship("UserSubject", back_populates="user")
    attempts = relationship("ChallengeAttempt", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")
    antifraud_events = relationship("AntifraudEvent", back_populates="user")
    competitions = relationship("CompetitionParticipant", back_populates="user")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    icon = Column(String(10), default="")
    color_from = Column(String(7), default="#007AFF")
    color_to = Column(String(7), default="#6000DD")
    created_at = Column(DateTime, default=utcnow)

    users = relationship("UserSubject", back_populates="subject")
    challenges = relationship("Challenge", back_populates="subject")
    questions = relationship("Question", back_populates="subject")


class UserSubject(Base):
    __tablename__ = "user_subjects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    progress_pct = Column(Float, default=0.0)
    questions_answered = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)

    user = relationship("User", back_populates="subjects")
    subject = relationship("Subject", back_populates="users")


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    xp_reward = Column(Integer, default=200)
    question_count = Column(Integer, default=5)
    is_daily = Column(Boolean, default=False)
    daily_date = Column(String(10), default="")
    created_at = Column(DateTime, default=utcnow)

    subject = relationship("Subject", back_populates="challenges")
    questions = relationship("Question", back_populates="challenge")
    attempts = relationship("ChallengeAttempt", back_populates="challenge")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)
    correct_answer_index = Column(Integer, nullable=False)
    xp_per_question = Column(Integer, default=40)
    difficulty = Column(String(20), default="medium")
    created_at = Column(DateTime, default=utcnow)

    challenge = relationship("Challenge", back_populates="questions")
    subject = relationship("Subject", back_populates="questions")
    answers = relationship("QuestionAnswer", back_populates="question")


class ChallengeAttempt(Base):
    __tablename__ = "challenge_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_id = Column(Integer, ForeignKey("challenges.id"), nullable=False)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)

    user = relationship("User", back_populates="attempts")
    challenge = relationship("Challenge", back_populates="attempts")
    answers = relationship("QuestionAnswer", back_populates="attempt")
    antifraud_events = relationship("AntifraudEvent", back_populates="attempt")


class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("challenge_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_answer = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_taken_seconds = Column(Float, default=0.0)
    answered_at = Column(DateTime, default=utcnow)

    attempt = relationship("ChallengeAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, default="")
    icon = Column(String(10), default="")
    condition_type = Column(String(50), nullable=False)
    condition_value = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    users = relationship("UserAchievement", back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="users")


class AntifraudEvent(Base):
    __tablename__ = "antifraud_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    attempt_id = Column(Integer, ForeignKey("challenge_attempts.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    details = Column(Text, default="")
    penalty_xp = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="antifraud_events")
    attempt = relationship("ChallengeAttempt", back_populates="antifraud_events")


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    comp_type = Column(String(50), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    status = Column(String(20), default="waiting")
    max_participants = Column(Integer, default=20)
    question_count = Column(Integer, default=5)
    time_limit_seconds = Column(Integer, default=30)
    created_at = Column(DateTime, default=utcnow)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    creator = relationship("User", foreign_keys=[creator_id])
    participants = relationship("CompetitionParticipant", back_populates="competition")


class CompetitionParticipant(Base):
    __tablename__ = "competition_participants"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, default=0)
    rank = Column(Integer, nullable=True)
    joined_at = Column(DateTime, default=utcnow)

    competition = relationship("Competition", back_populates="participants")
    user = relationship("User", back_populates="competitions")
