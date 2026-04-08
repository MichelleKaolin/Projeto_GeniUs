from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# ── Auth ──
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    university: str = ""
    course: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int


# ── User ──
class UserOut(BaseModel):
    id: int
    name: str
    email: str
    university: str
    course: str
    xp_total: int
    level: int
    streak_days: int
    streak_record: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: Optional[str] = None
    university: Optional[str] = None
    course: Optional[str] = None


class UserStats(BaseModel):
    xp_total: int
    level: int
    ranking_position: int
    accuracy_pct: float
    streak_days: int
    streak_record: int
    total_challenges: int
    total_questions_answered: int
    total_correct: int


# ── Subject ──
class SubjectOut(BaseModel):
    id: int
    name: str
    icon: str
    color_from: str
    color_to: str

    model_config = {"from_attributes": True}


class UserSubjectOut(BaseModel):
    subject: SubjectOut
    progress_pct: float
    questions_answered: int
    correct_answers: int

    model_config = {"from_attributes": True}


class SubjectToggle(BaseModel):
    subject_id: int


# ── Challenge ──
class QuestionOut(BaseModel):
    id: int
    question_text: str
    options: list[str]
    xp_per_question: int
    difficulty: str

    model_config = {"from_attributes": True}


class ChallengeOut(BaseModel):
    id: int
    title: str
    description: str
    xp_reward: int
    question_count: int
    subject: SubjectOut
    is_daily: bool
    questions: list[QuestionOut] = []

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    question_id: int
    selected_answer: int
    time_taken_seconds: float = 0.0


class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer_index: int
    xp_earned: int


class AttemptResult(BaseModel):
    id: int
    score: int
    total_questions: int
    correct_answers: int
    xp_earned: int
    is_completed: bool

    model_config = {"from_attributes": True}


# ── Leaderboard ──
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    name: str
    university: str
    xp_total: int
    level: int
    avatar_initial: str


# ── Achievement ──
class AchievementOut(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    condition_type: str
    condition_value: int

    model_config = {"from_attributes": True}


class UserAchievementOut(BaseModel):
    achievement: AchievementOut
    earned_at: datetime

    model_config = {"from_attributes": True}


# ── Anti-fraud ──
class AntifraudReport(BaseModel):
    attempt_id: Optional[int] = None
    event_type: str = Field(
        ..., description="copy_paste | tab_switch | screen_change | suspicious_speed"
    )
    details: str = ""


class AntifraudEventOut(BaseModel):
    id: int
    event_type: str
    details: str
    penalty_xp: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Competition ──
class CompetitionCreate(BaseModel):
    title: str
    comp_type: str = Field(
        ..., description="1v1 | tournament | flash_quiz"
    )
    subject_id: Optional[int] = None
    max_participants: int = 20
    question_count: int = 5
    time_limit_seconds: int = 30


class CompetitionOut(BaseModel):
    id: int
    title: str
    comp_type: str
    status: str
    max_participants: int
    question_count: int
    time_limit_seconds: int
    created_at: datetime
    participant_count: int = 0

    model_config = {"from_attributes": True}


class CompetitionParticipantOut(BaseModel):
    user_id: int
    name: str
    score: int
    rank: Optional[int]

    model_config = {"from_attributes": True}


# ── Dashboard ──
class DashboardOverview(BaseModel):
    xp_total: int
    level: int
    ranking_position: int
    accuracy_pct: float
    streak_days: int
    streak_record: int
    xp_today: int
    ranking_change: int
    daily_challenge: Optional[ChallengeOut] = None


class SubjectPerformance(BaseModel):
    subject_name: str
    subject_icon: str
    progress_pct: float
    questions_answered: int
    correct_answers: int
    accuracy_pct: float


class DailyActivity(BaseModel):
    date: str
    xp_earned: int
    questions_answered: int
    correct_answers: int


class DashboardAnalytics(BaseModel):
    subject_performance: list[SubjectPerformance]
    daily_activity: list[DailyActivity]
    total_study_time_minutes: float
    avg_accuracy_pct: float
    strongest_subject: str
    weakest_subject: str
