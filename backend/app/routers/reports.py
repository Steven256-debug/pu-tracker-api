import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Response

from ..auth import get_current_user
from ..recommendations import get_recommendations
from ..pdf_reports import generate_student_pdf, generate_cohort_pdf
from ..schemas import StudentPdfRequest, CohortPdfRequest

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/student-pdf")
def student_pdf(req: StudentPdfRequest, user: dict = Depends(get_current_user)):
    user_faculty = user.get("faculty")
    if user_faculty and req.student.get("faculty") != user_faculty:
        raise HTTPException(status_code=403, detail="Outside your faculty scope.")

    recs = req.student.get("recommendations")
    if recs:
        rec_tuples = [(r["icon"], r["text"]) for r in recs]
    else:
        rec_tuples = get_recommendations(req.student)

    pdf_bytes = generate_student_pdf(req.student, rec_tuples)
    if pdf_bytes is None:
        raise HTTPException(status_code=500, detail="reportlab is not installed on the server.")

    filename = f"report_{req.student.get('student_id', 'student')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/cohort-pdf")
def cohort_pdf(req: CohortPdfRequest, user: dict = Depends(get_current_user)):
    user_faculty = user.get("faculty")
    df = pd.DataFrame(req.students)
    if user_faculty and "faculty" in df.columns:
        df = df[df["faculty"] == user_faculty]

    pdf_bytes = generate_cohort_pdf(df, user.get("role", "Unknown"), user_faculty)
    if pdf_bytes is None:
        raise HTTPException(status_code=500, detail="reportlab is not installed on the server.")

    filename = f"cohort_report_{user_faculty or 'all'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
