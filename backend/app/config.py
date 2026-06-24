"""
Shared constants — ported exactly from the validated Streamlit app (app.py)
to guarantee identical behaviour. Do not change values here without also
updating the original Streamlit version and the project documentation.
"""

FACULTIES = ["FESAC", "FBA", "FEHAS", "PSTM"]
SEMESTERS = [
    "2019_S1", "2019_S2", "2020_S1", "2020_S2",
    "2021_S1", "2021_S2", "2022_S1", "2022_S2",
]

RISK_LABEL = {0: "Low Risk", 1: "Medium Risk", 2: "High Risk"}
RISK_ICON  = {0: "🟢", 1: "🟡", 2: "🔴"}
RISK_COLOR = {0: "#22c55e", 1: "#f59e0b", 2: "#ef4444"}
RISK_BG    = {0: "#102a1c", 1: "#2e2208", 2: "#2d0e0e"}

RISK_MEANING = {
    0: "This student is performing well and is not currently at risk of academic difficulty.",
    1: "This student shows some signs of academic difficulty. A check-in is recommended.",
    2: "This student is at significant risk of failing next semester. Immediate action is needed.",
}

FACULTY_FULL = {
    "FESAC": "Faculty of Engineering & Applied Sciences",
    "FBA":   "Faculty of Business Administration",
    "FEHAS": "Faculty of Education, Humanities & Applied Sciences",
    "PSTM":  "Pentecost School of Theology & Ministry",
}
FAC_COLOR = {
    "FESAC": "#60a5fa", "FBA": "#f59e0b", "FEHAS": "#22c55e", "PSTM": "#a78bfa",
}

# Exact order matters — must match feature_cols.json from the training notebook.
# This default is a fallback; the real artefact overrides it at load time.
DEFAULT_FEATURE_COLS = [
    "avg_attendance", "avg_total_mark", "avg_ca_score", "avg_exam_score",
    "total_credits", "num_courses", "gender_enc", "semester_index",
    "prev_gpa", "gpa_trend", "consec_fails", "trend_x_fail",
    "fac_FESAC", "fac_FBA", "fac_FEHAS", "fac_PSTM",
]

GRAD_CLASSES = [
    (3.60, 4.00, "First Class",        "#FFD700", "🥇"),
    (3.00, 3.59, "Second Class Upper", "#C0C0C0", "🥈"),
    (2.00, 2.99, "Second Class Lower", "#CD7F32", "🥉"),
    (1.50, 1.99, "Third Class",        "#f59e0b", "📜"),
    (1.00, 1.49, "Pass",               "#94a3b8", "📋"),
    (0.00, 0.99, "Fail",               "#ef4444", "❌"),
]

# Roles — faculty=None means unrestricted (Dean of Students)
ROLES = {
    "Academic Advisor — FESAC":  {"faculty": "FESAC", "icon": "👨‍🏫", "pwd_key": "ADVISOR_FESAC_PASSWORD",  "default": "advisor_fesac_2025", "tabs": ["predict"]},
    "Academic Advisor — FBA":    {"faculty": "FBA",   "icon": "👨‍🏫", "pwd_key": "ADVISOR_FBA_PASSWORD",    "default": "advisor_fba_2025",   "tabs": ["predict"]},
    "Academic Advisor — FEHAS":  {"faculty": "FEHAS", "icon": "👨‍🏫", "pwd_key": "ADVISOR_FEHAS_PASSWORD",  "default": "advisor_fehas_2025", "tabs": ["predict"]},
    "Academic Advisor — PSTM":   {"faculty": "PSTM",  "icon": "👨‍🏫", "pwd_key": "ADVISOR_PSTM_PASSWORD",   "default": "advisor_pstm_2025",  "tabs": ["predict"]},
    "Head of Department — FESAC": {"faculty": "FESAC", "icon": "🏛️", "pwd_key": "HOD_FESAC_PASSWORD", "default": "hod_fesac_2025", "tabs": ["predict", "analytics"]},
    "Head of Department — FBA":   {"faculty": "FBA",   "icon": "🏛️", "pwd_key": "HOD_FBA_PASSWORD",   "default": "hod_fba_2025",   "tabs": ["predict", "analytics"]},
    "Head of Department — FEHAS": {"faculty": "FEHAS", "icon": "🏛️", "pwd_key": "HOD_FEHAS_PASSWORD", "default": "hod_fehas_2025", "tabs": ["predict", "analytics"]},
    "Head of Department — PSTM":  {"faculty": "PSTM",  "icon": "🏛️", "pwd_key": "HOD_PSTM_PASSWORD",  "default": "hod_pstm_2025",  "tabs": ["predict", "analytics"]},
    "Dean of Students": {"faculty": None, "icon": "🎓", "pwd_key": "DEAN_PASSWORD", "default": "dean_2025", "tabs": ["predict", "analytics", "batch"]},
}
