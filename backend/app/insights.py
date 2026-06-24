"""
Cohort-level statistical insights — plain-English findings computed
directly from batch prediction results. Exact port of generate_insights()
from the validated Streamlit app. No model calls — pure arithmetic.
"""
from .config import FACULTIES, FACULTY_FULL


def generate_insights(df, faculty_filter) -> list:
    """Returns a list of (icon, color, headline, detail) tuples."""
    insights = []
    n = len(df)
    if n == 0:
        return insights

    # 1. Attendance risk multiplier
    if "avg_attendance" in df.columns and "risk_class" in df.columns:
        low_att = df[df["avg_attendance"] < 3.0]
        high_att = df[df["avg_attendance"] >= 3.0]
        if len(low_att) > 0 and len(high_att) > 0:
            low_att_hr_pct = (low_att["risk_class"] == 2).mean()
            high_att_hr_pct = (high_att["risk_class"] == 2).mean()
            if high_att_hr_pct > 0:
                mult = low_att_hr_pct / high_att_hr_pct
                insights.append((
                    "📉", "#ef4444",
                    f"Low attendance raises High Risk by {mult:.1f}×",
                    f"Students with attendance below 3.0 ({len(low_att):,} students) "
                    f"are {mult:.1f}× more likely to be High Risk than those above 3.0. "
                    f"Attendance is one of the strongest controllable risk factors."
                ))

    # 2. Highest-risk faculty
    if "faculty" in df.columns and "risk_class" in df.columns:
        fac_hr = {}
        for fac in FACULTIES:
            sub = df[df["faculty"] == fac]
            if len(sub) > 0:
                fac_hr[fac] = (sub["risk_class"] == 2).mean() * 100
        if fac_hr:
            worst_fac = max(fac_hr, key=fac_hr.get)
            best_fac = min(fac_hr, key=fac_hr.get)
            insights.append((
                "🏛️", "#f59e0b",
                f"{worst_fac} has the most High Risk students ({fac_hr[worst_fac]:.0f}%)",
                f"{FACULTY_FULL.get(worst_fac, worst_fac)} shows the highest proportion "
                f"of High Risk students at {fac_hr[worst_fac]:.0f}%, compared to "
                f"{best_fac} which has the lowest at {fac_hr[best_fac]:.0f}%. "
                f"This gap suggests {worst_fac} may need additional advisory resources."
            ))

    # 3. Consecutive decliners
    if "consec_fails" in df.columns:
        critical = df[df["consec_fails"] >= 2]
        if len(critical) > 0:
            insights.append((
                "⚠️", "#ef4444",
                f"{len(critical)} student{'s' if len(critical) != 1 else ''} "
                f"{'have' if len(critical) != 1 else 'has'} failed 2+ consecutive semesters",
                f"These {len(critical)} student{'s are' if len(critical) != 1 else ' is'} "
                f"at highest risk of academic probation. "
                f"Immediate counselling referral is strongly recommended before "
                f"the next semester begins."
            ))

    # 4. GPA trend alarm
    if "gpa_trend" in df.columns:
        sharp_decline = df[df["gpa_trend"] < -0.3]
        if len(sharp_decline) > 0:
            pct = len(sharp_decline) / n * 100
            insights.append((
                "📉", "#f59e0b",
                f"{len(sharp_decline)} student{'s' if len(sharp_decline) != 1 else ''} "
                f"({pct:.0f}%) show a sharp GPA decline this semester",
                f"A GPA drop of more than 0.3 points in one semester is a strong "
                f"early warning signal. These students have not necessarily failed yet, "
                f"but proactive outreach now is more effective than waiting for results."
            ))

    # 5. Gender performance gap
    if "gender" in df.columns and "semester_gpa" in df.columns:
        genders = df["gender"].str.strip().str.title().unique()
        if "Female" in genders and "Male" in genders:
            f_gpa = df[df["gender"].str.strip().str.title() == "Female"]["semester_gpa"].mean()
            m_gpa = df[df["gender"].str.strip().str.title() == "Male"]["semester_gpa"].mean()
            if f_gpa >= m_gpa:
                higher, h_val, lower, l_val = "Female", f_gpa, "Male", m_gpa
            else:
                higher, h_val, lower, l_val = "Male", m_gpa, "Female", f_gpa
            gap = abs(f_gpa - m_gpa)
            color = "#22c55e" if gap < 0.15 else "#f59e0b"
            insights.append((
                "👥", color,
                f"{'Minimal' if gap < 0.15 else 'Moderate'} gender performance gap "
                f"({gap:.2f} GPA points)",
                f"{higher} students average GPA {h_val:.2f} vs "
                f"{lower} students at {l_val:.2f}. "
                f"{'The gap is small — the model treats both groups equitably.' if gap < 0.15 else 'This gap warrants investigation to ensure equitable academic support.'}"
            ))

    # 6. Cohort health summary
    n_hr = (df["risk_class"] == 2).sum()
    n_lr = (df["risk_class"] == 0).sum()
    hr_pct = n_hr / n * 100
    if hr_pct >= 30:
        icon_c, clr = "🚨", "#ef4444"
        msg = f"Over {hr_pct:.0f}% of the cohort is High Risk — this semester demands urgent institutional attention."
    elif hr_pct >= 15:
        icon_c, clr = "🟡", "#f59e0b"
        msg = f"{hr_pct:.0f}% High Risk is above the typical threshold. Targeted faculty intervention is recommended."
    else:
        icon_c, clr = "🟢", "#22c55e"
        msg = f"At {hr_pct:.0f}% High Risk, the cohort is within manageable bounds. Continue standard monitoring."
    insights.append((
        icon_c, clr,
        f"Overall cohort health: {hr_pct:.0f}% High Risk, {n_lr / n * 100:.0f}% on track",
        msg
    ))

    return insights
