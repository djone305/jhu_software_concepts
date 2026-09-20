from sqlalchemy import select, func, case, or_, and_, desc
from models import SessionLocal, Applicant

def run_queries():
    # Open a SQLAlchemy session
    session = SessionLocal()
    
    try:
        print("==================================================")
        print("            SQLAlchemy ORM Query Results          ")
        print("==================================================\n")

        # --------------------------------------------------
        # Question 1: Fall 2026 applicant count
        # --------------------------------------------------
        stmt_q1 = select(func.count()).select_from(Applicant).where(
            Applicant.term.ilike('%Fall 2026%')
        )
        count_q1 = session.scalar(stmt_q1)
        print(f"Question 1: Fall 2026 applicant count")
        print(f"Result: {count_q1:,}\n")

        # --------------------------------------------------
        # Question 4: Average GPA of American applicants (Fall 2026)
        # --------------------------------------------------
        stmt_q4 = select(func.avg(Applicant.gpa)).where(
            and_(
                Applicant.term.ilike('%Fall 2026%'),
                Applicant.us_or_international.ilike('American')
            )
        )
        avg_gpa_q4 = session.scalar(stmt_q4)
        print(f"Question 4: Average GPA of American applicants (Fall 2026)")
        print(f"Result: {avg_gpa_q4:.2f}\n" if avg_gpa_q4 else "Result: N/A\n")

        # --------------------------------------------------
        # Question 5: Fall 2025 acceptance percentage
        # --------------------------------------------------
        accepted_case = case((Applicant.status.ilike('%Accept%'), 1), else_=0)
        stmt_q5 = select(
            (func.sum(accepted_case) * 100.0) / func.nullif(func.count(Applicant.p_id), 0)
        ).where(
            Applicant.term.ilike('%Fall 2025%')
        )
        pct_q5 = session.scalar(stmt_q5)
        print(f"Question 5: Fall 2025 acceptance percentage")
        print(f"Result: {pct_q5:.2f}%\n" if pct_q5 else "Result: N/A\n")

        # --------------------------------------------------
        # Question 8: Fall 2026 acceptances for PhD in CS at elite schools (Original Fields)
        # --------------------------------------------------
        stmt_q8 = select(func.count()).select_from(Applicant).where(
            and_(
                Applicant.term.ilike('%Fall 2026%'),
                Applicant.status.ilike('%Accept%'),
                or_(
                    Applicant.degree.ilike('%PhD%'),
                    Applicant.degree.op('~*')(r'\bPh\.?D\b')
                ),
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
        count_q8 = session.scalar(stmt_q8)
        print(f"Question 8: Fall 2026 PhD CS acceptances at elite schools (Original Fields)")
        print(f"Result: {count_q8}\n")

        # --------------------------------------------------
        # Question 9: Repeat Question 8 using LLM-generated fields
        # --------------------------------------------------
        stmt_q9 = select(func.count()).select_from(Applicant).where(
            and_(
                Applicant.term.ilike('%Fall 2026%'),
                Applicant.status.ilike('%Accept%'),
                or_(
                    Applicant.degree.ilike('%PhD%'),
                    Applicant.degree.op('~*')(r'\bPh\.?D\b')
                ),
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
        count_q9 = session.scalar(stmt_q9)
        diff = count_q8 - count_q9
        print(f"Question 9: Repeat Question 8 using LLM-generated fields")
        print(f"Result: Original count: {count_q8} | LLM count: {count_q9} | Difference: {diff}\n")

        # --------------------------------------------------
        # Custom Question 1: Average GPA of Fall 2026 PhD applicants grouped by status
        # --------------------------------------------------
        stmt_custom = select(
            Applicant.status,
            func.avg(Applicant.gpa).label('avg_gpa'),
            func.count().label('total_applicants')
        ).where(
            and_(
                Applicant.term.ilike('%Fall 2026%'),
                or_(
                    Applicant.degree.ilike('%PhD%'),
                    Applicant.degree.op('~*')(r'\bPh\.?D\b')
                ),
                Applicant.gpa.is_not(None),
                or_(
                    Applicant.status.ilike('%Accept%'),
                    Applicant.status.ilike('%Reject%'),
                    Applicant.status.ilike('%Wait%')
                )
            )
        ).group_by(
            Applicant.status
        ).order_by(
            desc('avg_gpa')
        )
        
        custom_results = session.execute(stmt_custom).all()
        print(f"Custom Question 1: Average GPA of Fall 2026 PhD applicants grouped by status")
        for row in custom_results:
            print(f" - Status: {row.status} | Avg GPA: {row.avg_gpa:.2f} | Count: {row.total_applicants:,}")
        print()

    finally:
        session.close()

if __name__ == "__main__":
    run_queries()