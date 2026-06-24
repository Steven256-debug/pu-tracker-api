"""
Model loading and prediction logic.

This is the ONLY part of the system that touches the trained LightGBM
model and scikit-learn scaler. It is a direct, behaviour-preserving port
of the prediction pipeline validated in the original Streamlit app
(run_batch_pipeline / predict_one). Do not change the feature engineering
order or formulas without re-validating against the original notebook.
"""
import pickle
import json
import os
from functools import lru_cache

import numpy as np
import pandas as pd

from .config import FACULTIES, SEMESTERS, RISK_LABEL, DEFAULT_FEATURE_COLS

ARTEFACT_DIR = os.environ.get("ARTEFACT_DIR", os.path.dirname(os.path.dirname(__file__)))


class ModelBundle:
    """Holds the loaded model, scaler, feature order, and thresholds."""
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_cols = DEFAULT_FEATURE_COLS
        self.thresholds = {}
        self.ready = False

    def load(self):
        try:
            with open(os.path.join(ARTEFACT_DIR, "best_model.pkl"), "rb") as f:
                self.model = pickle.load(f)
            with open(os.path.join(ARTEFACT_DIR, "scaler.pkl"), "rb") as f:
                self.scaler = pickle.load(f)
            with open(os.path.join(ARTEFACT_DIR, "feature_cols.json")) as f:
                self.feature_cols = json.load(f)
            with open(os.path.join(ARTEFACT_DIR, "thresholds.json")) as f:
                self.thresholds = json.load(f)
            self.ready = True
        except FileNotFoundError:
            self.ready = False
        return self

    @property
    def q33(self):
        return self.thresholds.get("Q33", 2.0)

    @property
    def q66(self):
        return self.thresholds.get("Q66", 3.0)

    @property
    def macro_f1(self):
        return self.thresholds.get("macro_f1", 0.6383)


@lru_cache(maxsize=1)
def get_model_bundle() -> ModelBundle:
    return ModelBundle().load()


def build_features(avg_attendance, avg_total_mark, avg_ca_score, avg_exam_score,
                    total_credits, num_courses, gender, semester_index,
                    prev_gpa, gpa_trend, consec_fails, faculty) -> dict:
    """Mirror the original build_features() exactly."""
    return {
        "avg_attendance": avg_attendance,
        "avg_total_mark": avg_total_mark,
        "avg_ca_score": avg_ca_score,
        "avg_exam_score": avg_exam_score,
        "total_credits": total_credits,
        "num_courses": num_courses,
        "gender_enc": int(gender == "Female"),
        "semester_index": semester_index,
        "prev_gpa": prev_gpa,
        "gpa_trend": gpa_trend,
        "consec_fails": consec_fails,
        "trend_x_fail": gpa_trend * consec_fails,
        "fac_FESAC": int(faculty == "FESAC"),
        "fac_FBA": int(faculty == "FBA"),
        "fac_FEHAS": int(faculty == "FEHAS"),
        "fac_PSTM": int(faculty == "PSTM"),
    }


def predict_one(feat_dict: dict, bundle: ModelBundle):
    """Scale and predict a single feature vector. Returns (class_int, probs ndarray)."""
    row = np.array([float(feat_dict.get(c, 0.0)) for c in bundle.feature_cols]).reshape(1, -1)
    row_sc = bundle.scaler.transform(row)
    probs = bundle.model.predict_proba(row_sc)[0]
    return int(np.argmax(probs)), probs


def run_batch_pipeline(df_raw: pd.DataFrame, bundle: ModelBundle) -> pd.DataFrame:
    """
    Exact port of the Streamlit app's run_batch_pipeline(). Applies the same
    feature engineering as the training notebook Cell 6, then runs the
    LightGBM model on every student-semester row.
    """
    df = df_raw.copy().sort_values(["student_id", "semester"])
    df["prev_gpa"] = df.groupby("student_id")["semester_gpa"].shift(1)
    df["gpa_trend"] = df["semester_gpa"] - df["prev_gpa"]
    df["is_fail"] = (df["semester_gpa"] < 1.5).astype(int)
    df["consec_fails"] = df.groupby("student_id")["is_fail"].transform(
        lambda x: x.rolling(window=2, min_periods=1).sum())
    df["trend_x_fail"] = df["gpa_trend"] * df["consec_fails"]
    for fac in FACULTIES:
        df[f"fac_{fac}"] = (df["faculty"] == fac).astype(int)
    df["gender_enc"] = (df["gender"].str.strip().str.title()
                         .map({"Female": 1, "Male": 0}).fillna(0).astype(int))
    sem_map = {s: i for i, s in enumerate(SEMESTERS)}
    df["semester_index"] = df["semester"].map(sem_map).fillna(0).astype(int)
    df = df.dropna(subset=["prev_gpa"]).reset_index(drop=True)

    X = df[bundle.feature_cols].fillna(0).values
    X_sc = bundle.scaler.transform(X)
    probs = bundle.model.predict_proba(X_sc)
    preds = probs.argmax(axis=1)

    df["risk_class"] = preds
    df["risk_label"] = [RISK_LABEL[p] for p in preds]
    df["prob_low"] = probs[:, 0].round(3)
    df["prob_med"] = probs[:, 1].round(3)
    df["prob_high"] = probs[:, 2].round(3)
    return df
