from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..model import get_model_bundle
from ..config import FAC_COLOR

router = APIRouter(prefix="/api/meta", tags=["meta"])

# SHAP feature importance — exact values ported from the validated notebook
# output (top_shap_features ranking), used for the Model Transparency panel.
SHAP_IMPORTANCE = [
    {"feature": "avg_total_mark", "importance": 0.382},
    {"feature": "avg_exam_score", "importance": 0.334},
    {"feature": "gpa_trend", "importance": 0.291},
    {"feature": "avg_ca_score", "importance": 0.238},
    {"feature": "consec_fails", "importance": 0.191},
    {"feature": "trend_x_fail", "importance": 0.153},
    {"feature": "fac_FEHAS", "importance": 0.122},
    {"feature": "prev_gpa", "importance": 0.096},
    {"feature": "fac_FESAC", "importance": 0.074},
    {"feature": "gender_enc", "importance": 0.051},
]

# Fairness audit — exact values ported from the validated notebook's
# intersectional Gender x Faculty audit (all groups pass the 0.45 threshold).
FAIRNESS_AUDIT = [
    {"group": "Female", "color": "#a78bfa", "macro_f1": 0.660},
    {"group": "Male", "color": "#60a5fa", "macro_f1": 0.613},
    {"group": "FESAC", "color": FAC_COLOR["FESAC"], "macro_f1": 0.869},
    {"group": "FBA", "color": FAC_COLOR["FBA"], "macro_f1": 0.801},
    {"group": "FEHAS", "color": FAC_COLOR["FEHAS"], "macro_f1": 0.582},
    {"group": "PSTM", "color": FAC_COLOR["PSTM"], "macro_f1": 0.666},
]

FAIRNESS_THRESHOLD = 0.45
ECE_SCORE = 0.0957  # Expected Calibration Error from the validated notebook


@router.get("/health")
def health():
    bundle = get_model_bundle()
    return {"status": "ok", "model_ready": bundle.ready}


@router.get("/model-info")
def model_info(user: dict = Depends(get_current_user)):
    bundle = get_model_bundle()
    return {
        "model_ready": bundle.ready,
        "macro_f1": bundle.macro_f1,
        "ece": ECE_SCORE,
        "q33": bundle.q33,
        "q66": bundle.q66,
        "n_features": len(bundle.feature_cols),
        "shap_importance": SHAP_IMPORTANCE,
        "fairness_audit": FAIRNESS_AUDIT,
        "fairness_threshold": FAIRNESS_THRESHOLD,
    }
