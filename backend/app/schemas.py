"""Pydantic schemas for all API requests and responses."""
from typing import Optional, List
from pydantic import BaseModel


# ── Auth ─────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    role: str
    password: str


class LoginResponse(BaseModel):
    token: str
    role: str
    faculty: Optional[str]
    icon: str
    tabs: List[str]


# ── Individual prediction ───────────────────────────────────────────────
class PredictRequest(BaseModel):
    student_id: Optional[str] = ""
    name: Optional[str] = ""
    faculty: str
    gender: str
    semester_index: int
    avg_attendance: float
    avg_total_mark: float
    avg_ca_score: float
    avg_exam_score: float
    total_credits: int
    num_courses: int
    prev_gpa: float
    gpa_trend: float
    consec_fails: int
    # Optional graduation inputs
    level: Optional[str] = None
    cumulative_gpa: Optional[float] = None
    completed_credits: Optional[int] = None
    programme_credits: Optional[int] = None


class PredictResponse(BaseModel):
    risk_class: int
    risk_label: str
    prob_low: float
    prob_med: float
    prob_high: float
    recommendations: List[dict]
    graduation: Optional[dict] = None
    trajectory: Optional[list] = None
    trajectory_insight: Optional[dict] = None


# ── Simulator ────────────────────────────────────────────────────────────
class SimulateRequest(PredictRequest):
    pass


# ── Batch ────────────────────────────────────────────────────────────────
class BatchSummary(BaseModel):
    n: int
    n_high: int
    n_medium: int
    n_low: int
    avg_gpa: float


class BatchResponse(BaseModel):
    students: List[dict]
    summary: BatchSummary
    insights: List[dict]
    graduation_summary: List[dict]


# ── PDF requests ─────────────────────────────────────────────────────────
class StudentPdfRequest(BaseModel):
    student: dict


class CohortPdfRequest(BaseModel):
    students: List[dict]
