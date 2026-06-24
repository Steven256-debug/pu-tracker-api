"""
PDF report generation. This is the second (and last) place Python is
required by necessity — reportlab has no equivalent fidelity in the
browser. Exact port of generate_pdf() and generate_cohort_pdf() from the
validated Streamlit app.
"""
import io
import datetime

from .config import FACULTY_FULL, FACULTIES
from .graduation import graduation_summary
from .insights import generate_insights


def generate_student_pdf(row: dict, recs: list) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                         Spacer, Table, TableStyle, HRFlowable)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                 rightMargin=2 * cm, leftMargin=2 * cm,
                                 topMargin=2 * cm, bottomMargin=2 * cm)
        ss = getSampleStyleSheet()
        BLUE = colors.HexColor("#4f7cff")
        GREY = colors.HexColor("#666")
        LIGHT = colors.HexColor("#f0f4f8")
        story = []

        def p(txt, size=10, bold=False, color=colors.HexColor("#333"), after=8, align=0):
            return Paragraph(txt, ParagraphStyle("p", parent=ss["Normal"],
                fontSize=size, fontName="Helvetica-Bold" if bold else "Helvetica",
                textColor=color, spaceAfter=after, alignment=align))

        def section(txt):
            return Paragraph(txt, ParagraphStyle("h", parent=ss["Heading2"],
                fontSize=13, textColor=BLUE, fontName="Helvetica-Bold",
                spaceBefore=14, spaceAfter=6))

        story += [
            p("PENTECOST UNIVERSITY", 18, True, BLUE, after=4, align=1),
            p("AI Academic Performance Tracker — Student Risk Report", 10,
              color=GREY, after=16, align=1),
            HRFlowable(width="100%", thickness=2, color=BLUE),
            Spacer(1, 10),
        ]

        risk_class = row.get("risk_class", 0)
        rc_colors = {0: colors.HexColor("#27ae60"),
                     1: colors.HexColor("#f39c12"),
                     2: colors.HexColor("#e74c3c")}
        rc_color = rc_colors.get(int(risk_class), GREY)

        story.append(section("Student Information"))
        info = Table([
            ["Student ID", str(row.get("student_id", "N/A")),
             "Name", str(row.get("name", "N/A"))],
            ["Faculty", FACULTY_FULL.get(str(row.get("faculty", "")), str(row.get("faculty", "N/A"))),
             "Semester", str(row.get("semester", "N/A"))],
            ["Gender", str(row.get("gender", "N/A")),
             "Date", datetime.date.today().strftime("%d %B %Y")],
        ], colWidths=[3.5 * cm, 5.5 * cm, 3.5 * cm, 5.5 * cm])
        info.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), BLUE),
            ("TEXTCOLOR", (2, 0), (2, -1), BLUE),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, colors.white]),
        ]))
        story += [info, Spacer(1, 12)]

        story.append(section("Risk Assessment Result"))
        res = Table([
            ["Risk Level", row.get("risk_label", "N/A"),
             "Confidence", f"{max(row.get('prob_low', 0), row.get('prob_med', 0), row.get('prob_high', 0)):.0%}"],
            ["Low Risk", f"{row.get('prob_low', 0):.0%}",
             "Medium Risk", f"{row.get('prob_med', 0):.0%}"],
            ["High Risk", f"{row.get('prob_high', 0):.0%}",
             "Previous GPA", f"{row.get('prev_gpa', 0):.2f}"],
        ], colWidths=[3.5 * cm, 5.5 * cm, 3.5 * cm, 5.5 * cm])
        res.setStyle(TableStyle([
            ("BACKGROUND", (1, 0), (1, 0), rc_color),
            ("TEXTCOLOR", (1, 0), (1, 0), colors.white),
            ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), BLUE),
            ("TEXTCOLOR", (2, 0), (2, -1), BLUE),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT, colors.white]),
        ]))
        story += [res, Spacer(1, 12)]

        story.append(section("Recommended Actions"))
        for i, (icon, text) in enumerate(recs, 1):
            story.append(p(f"{i}. {text}", after=6))

        story += [
            Spacer(1, 20),
            HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")),
            Spacer(1, 6),
            p(f"Pentecost University | AI Academic Performance Tracker | "
              f"Ghana DPA 2012 (Act 843) | "
              f"{datetime.datetime.now().strftime('%d %B %Y %H:%M')}",
              size=7.5, color=GREY, align=1),
        ]
        doc.build(story)
        return buf.getvalue()
    except ImportError:
        return None


def generate_cohort_pdf(df, role: str, faculty_filter) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                         Spacer, Table, TableStyle, HRFlowable)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                 rightMargin=2 * cm, leftMargin=2 * cm,
                                 topMargin=1.8 * cm, bottomMargin=1.8 * cm)
        ss = getSampleStyleSheet()
        BLUE = colors.HexColor("#1F4E79")
        DGREY = colors.HexColor("#666666")
        LIGHT = colors.HexColor("#f0f4f8")
        RED = colors.HexColor("#e74c3c")
        GRID = colors.HexColor("#dee2e6")
        story = []

        def para(txt, size=10, bold=False, color=colors.HexColor("#333"), after=6, align=0):
            return Paragraph(txt, ParagraphStyle("p", parent=ss["Normal"],
                fontSize=size, fontName="Helvetica-Bold" if bold else "Helvetica",
                textColor=color, spaceAfter=after, alignment=align))

        def section(txt):
            return Paragraph(txt, ParagraphStyle("h2", parent=ss["Heading2"],
                fontSize=12, fontName="Helvetica-Bold", textColor=BLUE,
                spaceBefore=14, spaceAfter=6,
                borderPad=4, backColor=colors.HexColor("#EBF2FA")))

        def make_table(data, col_widths, hdr_color=BLUE):
            t = Table(data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), hdr_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, GRID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, colors.white]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            return t

        n = len(df)
        n_hr = int((df["risk_class"] == 2).sum()) if "risk_class" in df.columns else 0
        n_mr = int((df["risk_class"] == 1).sum()) if "risk_class" in df.columns else 0
        n_lr = int((df["risk_class"] == 0).sum()) if "risk_class" in df.columns else 0
        scope = FACULTY_FULL.get(faculty_filter, "All Faculties") if faculty_filter else "All Faculties"

        story += [
            para("PENTECOST UNIVERSITY", 20, True, BLUE, after=4, align=1),
            para("AI Academic Performance Tracker — Cohort Risk Report", 11, False, DGREY, after=4, align=1),
            para(f"Faculty Scope: {scope}", 10, False, DGREY, after=4, align=1),
            para(f"Prepared for: {role}  |  Date: {datetime.date.today().strftime('%d %B %Y')}",
                 9, False, DGREY, after=10, align=1),
            HRFlowable(width="100%", thickness=2, color=BLUE),
            Spacer(1, 10),
        ]

        story.append(section("Executive Summary"))
        hr_pct = n_hr / n * 100 if n > 0 else 0
        avg_gpa = df["semester_gpa"].mean() if "semester_gpa" in df.columns else 0
        summary_data = [
            ["Metric", "Value", "Metric", "Value"],
            ["Total Students Assessed", f"{n:,}", "Average Cohort GPA", f"{avg_gpa:.2f}"],
            ["High Risk", f"{n_hr:,} ({hr_pct:.0f}%)",
             "Medium Risk", f"{n_mr:,} ({n_mr / n * 100:.0f}%)" if n > 0 else "0"],
            ["Low Risk / On Track", f"{n_lr:,} ({n_lr / n * 100:.0f}%)" if n > 0 else "0",
             "Semester", str(df["semester"].mode()[0]) if "semester" in df.columns else "N/A"],
        ]
        story.append(make_table(summary_data, [4 * cm, 5 * cm, 4 * cm, 5 * cm]))
        story.append(Spacer(1, 10))

        if "faculty" in df.columns:
            story.append(section("Risk Distribution by Faculty"))
            fac_rows = [["Faculty", "Total", "High Risk", "Medium Risk", "Low Risk", "High Risk %"]]
            for fac in FACULTIES:
                sub = df[df["faculty"] == fac]
                if len(sub) == 0:
                    continue
                fn = len(sub)
                fhr = (sub["risk_class"] == 2).sum() if "risk_class" in sub.columns else 0
                fmr = (sub["risk_class"] == 1).sum() if "risk_class" in sub.columns else 0
                flr = (sub["risk_class"] == 0).sum() if "risk_class" in sub.columns else 0
                fac_rows.append([fac, str(fn), str(int(fhr)), str(int(fmr)),
                                  str(int(flr)), f"{fhr / fn * 100:.0f}%"])
            story.append(make_table(fac_rows, [3 * cm, 2.2 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.3 * cm]))
            story.append(Spacer(1, 10))

        if "gender" in df.columns:
            story.append(section("Gender Performance Breakdown"))
            genders = [g for g in ["Female", "Male"] if g in df["gender"].str.strip().str.title().unique()]
            g_rows = [["Gender", "Count", "Avg GPA", "High Risk", "Medium Risk", "Low Risk"]]
            for g in genders:
                sub = df[df["gender"].str.strip().str.title() == g]
                fn = len(sub)
                gg = sub["semester_gpa"].mean() if "semester_gpa" in sub.columns else 0
                ghr = (sub["risk_class"] == 2).sum() if "risk_class" in sub.columns else 0
                gmr = (sub["risk_class"] == 1).sum() if "risk_class" in sub.columns else 0
                glr = (sub["risk_class"] == 0).sum() if "risk_class" in sub.columns else 0
                g_rows.append([g, str(fn), f"{gg:.2f}", str(int(ghr)), str(int(gmr)), str(int(glr))])
            story.append(make_table(g_rows, [3.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm]))
            story.append(Spacer(1, 10))

        story.append(section("Top 15 Highest-Risk Students"))
        story.append(para(
            "The following students have the highest predicted probability of "
            "academic failure next semester and require priority advisory attention.",
            9, color=DGREY, after=6))

        if "prob_high" in df.columns and "risk_class" in df.columns:
            top15 = (df[df["risk_class"] == 2].sort_values("prob_high", ascending=False).head(15))
            if len(top15) > 0:
                show_cols = [c for c in ["student_id", "name", "faculty", "semester_gpa", "prob_high"]
                             if c in top15.columns]
                headers = {"student_id": "ID", "name": "Name", "faculty": "Faculty",
                           "semester_gpa": "GPA", "prob_high": "Risk Prob"}
                t_data = [[headers.get(c, c) for c in show_cols]]
                for _, row in top15.iterrows():
                    t_data.append([
                        str(row.get("student_id", "")),
                        str(row.get("name", ""))[:22],
                        str(row.get("faculty", "")),
                        f"{row.get('semester_gpa', 0):.2f}",
                        f"{row.get('prob_high', 0):.0%}",
                    ])
                col_w = [2 * cm, 5.5 * cm, 2.5 * cm, 2 * cm, 2.5 * cm]
                t = Table(t_data, colWidths=col_w)
                row_bgs = []
                for i in range(1, len(t_data)):
                    c = colors.HexColor("#fde8e8") if i % 2 == 0 else LIGHT
                    row_bgs.append(("BACKGROUND", (0, i), (-1, i), c))
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), RED),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("PADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, GRID),
                    ("TEXTCOLOR", (-1, 1), (-1, -1), RED),
                    ("FONTNAME", (-1, 1), (-1, -1), "Helvetica-Bold"),
                ] + row_bgs))
                story.append(t)
            else:
                story.append(para("No High Risk students in current dataset.", 9))

        story.append(Spacer(1, 10))

        grad_df = graduation_summary(df)
        if len(grad_df) > 0:
            story.append(section("Graduation Classification Projections (Level 300/400)"))
            class_counts = grad_df["Classification"].value_counts()
            c_rows = [["Classification", "Count"]]
            for cls, cnt in class_counts.items():
                c_rows.append([cls, str(cnt)])
            story.append(make_table(c_rows, [12 * cm, 3 * cm]))
            story.append(Spacer(1, 8))

        insights = generate_insights(df, faculty_filter)
        if insights:
            story.append(section("Key Findings"))
            for i, (icon, color, headline, detail) in enumerate(insights, 1):
                story.append(para(f"<b>{i}. {headline}</b>", 9, color=BLUE, after=3))
                story.append(para(detail, 9, color=DGREY, after=8))

        story += [
            Spacer(1, 16),
            HRFlowable(width="100%", thickness=1, color=colors.HexColor("#dee2e6")),
            Spacer(1, 5),
            para(f"Pentecost University | AI Academic Performance Tracker | "
                 f"Ghana DPA 2012 (Act 843) | "
                 f"Generated: {datetime.datetime.now().strftime('%d %B %Y %H:%M')}",
                 7.5, color=DGREY, after=0, align=1),
        ]

        doc.build(story)
        return buf.getvalue()
    except ImportError:
        return None
