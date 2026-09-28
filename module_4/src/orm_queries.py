# In orm_queries.py
from sqlalchemy import select, func, case, or_, and_, desc
from models import SessionLocal, Applicant

def get_analysis_data():
    session = SessionLocal()
    try:
        # Question 1
        q1 = session.scalar(
            select(func.count()).select_from(Applicant).where(Applicant.term.ilike('%Fall 2026%'))
        )

        # Question 4
        avg_gpa = session.scalar(
            select(func.avg(Applicant.gpa)).where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    Applicant.us_or_international.ilike('American')
                )
            )
        )
        q4 = round(avg_gpa, 2) if avg_gpa else "N/A"

        # Question 5
        accepted_case = case((Applicant.status.ilike('%Accept%'), 1), else_=0)
        q5_val = session.scalar(
            select((func.sum(accepted_case) * 100.0) / func.nullif(func.count(Applicant.p_id), 0))
            .where(Applicant.term.ilike('%Fall 2025%'))
        )
        q5 = f"{q5_val:.2f}%" if q5_val else "N/A"

        # Question 8
        q8 = session.scalar(
            select(func.count()).select_from(Applicant).where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    Applicant.status.ilike('%Accept%'),
                    or_(Applicant.degree.ilike('%PhD%'), Applicant.degree.op('~*')(r'\bPh\.?D\b')),
                    Applicant.program.ilike('%Computer Science%'),
                    or_(
                        Applicant.program.ilike('%Georgetown%'),
                        Applicant.program.ilike('%Massachusetts Institute of Technology%'),
                        Applicant.program.op('~*')(r'\bMIT\b'),
                        Applicant.program.ilike('%Stanford%'),
                        Applicant.program.ilike('%Carnegie Mellon%'),
                        Applicant.program.op('~*')(r'\bCMU\b')
                    )
                )
            )
        )

        # Question 9
        q9 = session.scalar(
            select(func.count()).select_from(Applicant).where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    Applicant.status.ilike('%Accept%'),
                    or_(Applicant.degree.ilike('%PhD%'), Applicant.degree.op('~*')(r'\bPh\.?D\b')),
                    Applicant.llm_generated_program.ilike('%Computer Science%'),
                    or_(
                        Applicant.llm_generated_university.ilike('%Georgetown%'),
                        Applicant.llm_generated_university.ilike('%Massachusetts Institute of Technology%'),
                        Applicant.llm_generated_university.op('~*')(r'\bMIT\b'),
                        Applicant.llm_generated_university.ilike('%Stanford%'),
                        Applicant.llm_generated_university.ilike('%Carnegie Mellon%'),
                        Applicant.llm_generated_university.op('~*')(r'\bCMU\b')
                    )
                )
            )
        )

        # Custom Question 1
        normalized_status = case(
            (Applicant.status.ilike('%Wait%'), 'Waitlisted'),
            (Applicant.status.ilike('%Accept%'), 'Accepted'),
            (Applicant.status.ilike('%Reject%'), 'Rejected'),
            else_='Other'
        ).label('clean_status')

        cq1_rows = session.execute(
            select(
                normalized_status,
                func.avg(Applicant.gpa).label('avg_gpa'),
                func.count().label('total')
            ).where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    or_(Applicant.degree.ilike('%PhD%'), Applicant.degree.op('~*')(r'\bPh\.?D\b')),
                    Applicant.gpa.is_not(None)
                )
            ).group_by(normalized_status).order_by(desc('avg_gpa'))
        ).all()

        cq1 = [{"status": r.clean_status, "gpa": f"{r.avg_gpa:.2f}", "count": r.total} for r in cq1_rows]

        # Custom Question 2
        cq2_rows = session.execute(
            select(
                Applicant.us_or_international,
                func.count(Applicant.p_id)
            ).where(Applicant.term.ilike('%Fall 2026%'))
            .group_by(Applicant.us_or_international)
        ).all()

        cq2 = [{"type": r[0] if r[0] else "Unknown", "count": r[1]} for r in cq2_rows]

        return {
            "q1": q1,
            "q4": q4,
            "q5": q5,
            "q8": q8,
            "q9": q9,
            "cq1": cq1,
            "cq2": cq2
        }
    finally:
        session.close()