"""
Graduation classification projection + multi-semester trajectory.
Exact port of project_graduation / get_grad_class / project_trajectory /
trajectory_insight from the validated Streamlit app.
"""
from .config import GRAD_CLASSES


def get_grad_class(cgpa: float):
    for low, high, label, color, emoji in GRAD_CLASSES:
        if low <= round(cgpa, 3) <= high:
            return label, color, emoji
    return "Fail", "#ef4444", "❌"


def project_graduation(cum_gpa, gpa_trend, level_num, comp_cr, prog_cr) -> dict:
    remaining = 2 if level_num == 300 else 1
    rem_cr = max(0, prog_cr - comp_cr)
    proj_sem = min(4.0, max(0.0, cum_gpa + gpa_trend * 0.5 * remaining))
    if prog_cr > 0:
        proj = (comp_cr * cum_gpa + rem_cr * proj_sem) / prog_cr
    else:
        proj = cum_gpa
    proj = round(min(4.0, max(0.0, proj)), 3)
    label, color, emoji = get_grad_class(proj)

    next_cls = []
    for low, high, cls, clr, emj in GRAD_CLASSES:
        if low > proj and rem_cr > 0:
            needed = ((low * prog_cr) - (comp_cr * cum_gpa)) / rem_cr
            needed = round(needed, 2)
            if 0.0 <= needed <= 4.0:
                next_cls.append({"class": cls, "color": clr, "emoji": emj,
                                  "needed": needed, "target": low})

    return {
        "proj_cgpa": proj, "label": label, "color": color, "emoji": emoji,
        "remaining": remaining, "next": next_cls[:2],
    }


def project_trajectory(current_gpa: float, gpa_trend: float, q33: float,
                        q66: float, n_steps: int = 4) -> list:
    """
    Project a student's GPA forward n_steps semesters assuming the current
    GPA trend continues at half its observed rate each semester (the same
    dampening assumption used in project_graduation).
    """
    delta = gpa_trend * 0.5
    points = []
    gpa = current_gpa
    for step in range(n_steps + 1):
        if step > 0:
            gpa = min(4.0, max(0.0, gpa + delta))
        zone = 2 if gpa < q33 else (1 if gpa < q66 else 0)
        points.append({"step": step, "gpa": round(gpa, 3), "zone": zone})
    return points


def trajectory_insight(points: list, name: str = "This student") -> tuple:
    """Returns (icon, message) describing the trajectory in plain English."""
    zone_label = {0: "Low Risk", 1: "Medium Risk", 2: "High Risk"}
    current_zone = points[0]["zone"]

    for p in points[1:]:
        if p["zone"] != current_zone:
            if p["zone"] < current_zone:
                return ("📈", f"{name} is projected to improve from "
                              f"{zone_label[current_zone]} into "
                              f"{zone_label[p['zone']]} within {p['step']} "
                              f"semester(s) if the current trend continues.")
            else:
                return ("📉", f"{name} is projected to decline from "
                              f"{zone_label[current_zone]} into "
                              f"{zone_label[p['zone']]} within {p['step']} "
                              f"semester(s) if nothing changes. Early "
                              f"intervention now could change this trajectory.")

    return ("➡️", f"{name} is projected to remain in the "
                  f"{zone_label[current_zone]} zone over the next "
                  f"{points[-1]['step']} semesters if current patterns continue.")


def graduation_summary(df) -> "pd.DataFrame":
    """Graduation projection table for Level 300/400 students."""
    import pandas as pd
    if "level" not in df.columns:
        return pd.DataFrame()
    final = df[df["level"].isin(["Level 300", "Level 400"])].copy()
    if len(final) == 0:
        return pd.DataFrame()
    rows = []
    for _, row in final.iterrows():
        lv = int(str(row.get("level", "300")).split()[-1])
        cum = row.get("cumulative_gpa", row.get("prev_gpa", 1.8))
        comp = row.get("completed_credits", 90)
        prog = row.get("programme_credits", 120)
        gtr = row.get("gpa_trend", 0)
        grad = project_graduation(cum, gtr, lv, comp, prog)
        rows.append({
            "Student ID": row.get("student_id", ""),
            "Name": row.get("name", ""),
            "Faculty": row.get("faculty", ""),
            "Level": row.get("level", ""),
            "Current CGPA": round(cum, 2),
            "Projected CGPA": grad["proj_cgpa"],
            "Classification": grad["emoji"] + "  " + grad["label"],
            "Risk Level": row.get("risk_label", ""),
        })
    return pd.DataFrame(rows)
