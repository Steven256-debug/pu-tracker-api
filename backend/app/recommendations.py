"""
Rule-based recommendation engine — separate from the ML model.
Exact port of get_recommendations() from the validated Streamlit app.
"""


def get_recommendations(row: dict) -> list:
    recs = []
    att = row.get("avg_attendance", 0)
    exam = row.get("avg_exam_score", 0)
    ca = row.get("avg_ca_score", 0)
    trend = row.get("gpa_trend", 0)
    cf = row.get("consec_fails", 0)
    pgpa = row.get("prev_gpa", 0)

    if att < 3.0:
        recs.append(("🔴", f"Attendance is very low ({att:.1f}/5). "
                            "Contact the student immediately to understand the reason "
                            "and create an attendance plan."))
    elif att < 3.5:
        recs.append(("🟡", f"Attendance ({att:.1f}/5) is below the recommended level. "
                            "Remind the student that attendance directly affects their grades."))

    if exam / 60 < 0.4:
        recs.append(("🔴", f"Exam performance is critically low ({exam:.0f}/60). "
                            "Refer the student to the Academic Support Centre for exam preparation help."))
    elif exam / 60 < 0.5:
        recs.append(("🟡", f"Exam scores ({exam:.0f}/60) are below average. "
                            "Encourage the student to join study groups and seek help from lecturers."))

    if ca / 40 < 0.5:
        recs.append(("🟡", f"Continuous Assessment score ({ca:.0f}/40) is below average. "
                            "Check that all assignments have been submitted on time."))

    if trend < -0.2:
        recs.append(("🔴", "The student's GPA has dropped significantly. "
                            "Schedule an urgent meeting to understand what is affecting their performance."))
    elif trend < 0:
        recs.append(("🟡", "The student's GPA is slowly declining. "
                            "A check-in meeting is recommended before the situation worsens."))

    if cf >= 2:
        recs.append(("🔴", f"This student has had a GPA below 1.5 for {int(cf)} "
                            "semesters in a row. Consider referring to the counselling service "
                            "and reviewing their course selection."))

    if not recs:
        recs.append(("🟢", "This student is performing well. "
                            "Continue standard monitoring through the regular review process."))

    return recs[:5]
