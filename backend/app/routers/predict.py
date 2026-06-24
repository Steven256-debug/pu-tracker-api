import io

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from ..auth import get_current_user, enforce_faculty_scope
from ..model import get_model_bundle, build_features, predict_one, run_batch_pipeline
from ..recommendations import get_recommendations
from ..graduation import (project_graduation, project_trajectory,
                           trajectory_insight, graduation_summary)
from ..insights import generate_insights
from ..schemas import PredictRequest, PredictResponse, SimulateRequest, BatchResponse

router = APIRouter(prefix="/api/predict", tags=["predict"])


def _check_model_ready():
    bundle = get_model_bundle()
    if not bundle.ready:
        raise HTTPException(
            status_code=503,
            detail="Model artefacts not found on the server. "
                   "Upload best_model.pkl, scaler.pkl, feature_cols.json, "
                   "thresholds.json to the backend deployment.",
        )
    return bundle


def _check_faculty_access(user: dict, faculty: str):
    """A scoped role cannot predict for a faculty outside their own."""
    user_faculty = user.get("faculty")
    if user_faculty is not None and faculty != user_faculty:
        raise HTTPException(
            status_code=403,
            detail=f"Your role is restricted to {user_faculty}. "
                   f"You cannot submit predictions for {faculty}.",
        )


def _predict_payload(req: PredictRequest, bundle) -> tuple:
    feats = build_features(
        req.avg_attendance, req.avg_total_mark, req.avg_ca_score, req.avg_exam_score,
        req.total_credits, req.num_courses, req.gender, req.semester_index,
        req.prev_gpa, req.gpa_trend, req.consec_fails, req.faculty,
    )
    pred, probs = predict_one(feats, bundle)
    recs = get_recommendations(feats)

    grad = None
    if req.level in ("Level 300", "Level 400") and req.cumulative_gpa is not None:
        lv_num = int(req.level.split()[1])
        grad = project_graduation(
            req.cumulative_gpa, req.gpa_trend, lv_num,
            req.completed_credits or 90, req.programme_credits or 120,
        )

    traj = project_trajectory(req.prev_gpa, req.gpa_trend, bundle.q33, bundle.q66)
    t_icon, t_msg = trajectory_insight(traj, req.name or "This student")

    return feats, pred, probs, recs, grad, traj, {"icon": t_icon, "message": t_msg}


@router.post("/individual", response_model=PredictResponse)
def predict_individual(req: PredictRequest, user: dict = Depends(get_current_user)):
    bundle = _check_model_ready()
    _check_faculty_access(user, req.faculty)

    feats, pred, probs, recs, grad, traj, t_insight = _predict_payload(req, bundle)

    return PredictResponse(
        risk_class=pred,
        risk_label=["Low Risk", "Medium Risk", "High Risk"][pred],
        prob_low=round(float(probs[0]), 4),
        prob_med=round(float(probs[1]), 4),
        prob_high=round(float(probs[2]), 4),
        recommendations=[{"icon": i, "text": t} for i, t in recs],
        graduation=grad,
        trajectory=traj,
        trajectory_insight=t_insight,
    )


@router.post("/simulate", response_model=PredictResponse)
def predict_simulate(req: SimulateRequest, user: dict = Depends(get_current_user)):
    """
    Powers the What-If Simulator. Identical to /individual but kept as a
    separate endpoint so the frontend can clearly distinguish "this is a
    hypothetical re-run" from "this is the official saved prediction."
    """
    bundle = _check_model_ready()
    _check_faculty_access(user, req.faculty)

    feats, pred, probs, recs, grad, traj, t_insight = _predict_payload(req, bundle)

    return PredictResponse(
        risk_class=pred,
        risk_label=["Low Risk", "Medium Risk", "High Risk"][pred],
        prob_low=round(float(probs[0]), 4),
        prob_med=round(float(probs[1]), 4),
        prob_high=round(float(probs[2]), 4),
        recommendations=[{"icon": i, "text": t} for i, t in recs],
        graduation=grad,
        trajectory=traj,
        trajectory_insight=t_insight,
    )


@router.post("/batch", response_model=BatchResponse)
async def predict_batch(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    bundle = _check_model_ready()

    try:
        raw_bytes = await file.read()
        df_raw = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read CSV file: {e}")

    required_cols = {"student_id", "faculty", "gender", "semester", "semester_gpa",
                      "avg_attendance", "avg_total_mark", "avg_ca_score",
                      "avg_exam_score", "total_credits", "num_courses"}
    missing = required_cols - set(df_raw.columns)
    if missing:
        raise HTTPException(status_code=400,
                             detail=f"CSV is missing required columns: {sorted(missing)}")

    # A scoped role only ever sees and predicts on their own faculty's rows,
    # enforced server-side regardless of what the uploaded file contains.
    user_faculty = user.get("faculty")
    if user_faculty:
        df_raw = df_raw[df_raw["faculty"] == user_faculty].copy()

    df = run_batch_pipeline(df_raw, bundle)
    if len(df) == 0:
        raise HTTPException(
            status_code=400,
            detail="No rows survived processing. Each student needs at least "
                   "2 semester rows so the system can compute a GPA trend.",
        )

    # Add recommendations per row (kept lightweight — only icon+text)
    rec_lists = df.to_dict("records")
    for row in rec_lists:
        row["recommendations"] = [{"icon": i, "text": t} for i, t in get_recommendations(row)]
        # Clean NaN -> None for JSON
        for k, v in list(row.items()):
            if isinstance(v, float) and np.isnan(v):
                row[k] = None

    n = len(df)
    n_hr = int((df["risk_class"] == 2).sum())
    n_mr = int((df["risk_class"] == 1).sum())
    n_lr = int((df["risk_class"] == 0).sum())
    avg_gpa = float(df["semester_gpa"].mean()) if "semester_gpa" in df.columns else 0.0

    insights = generate_insights(df, user_faculty)
    insight_payload = [
        {"icon": i, "color": c, "headline": h, "detail": d}
        for i, c, h, d in insights
    ]

    grad_df = graduation_summary(df)
    grad_payload = grad_df.to_dict("records") if len(grad_df) else []

    return BatchResponse(
        students=rec_lists,
        summary={"n": n, "n_high": n_hr, "n_medium": n_mr, "n_low": n_lr, "avg_gpa": round(avg_gpa, 3)},
        insights=insight_payload,
        graduation_summary=grad_payload,
    )
