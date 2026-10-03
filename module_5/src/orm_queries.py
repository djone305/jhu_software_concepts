import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select, func, case, or_, and_, desc
from sqlalchemy.orm import sessionmaker

# Import model definition from models.py
from models import Applicant

# Load environment variables
load_dotenv()

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "grad_admissions")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if not DB_PASSWORD: # pragma: no cover
    raise ValueError("Missing database password! Set the DB_PASSWORD environment variable.")

# Construct Database URL for SQLAlchemy
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Setup Engine and Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Formatting Helpers ---
def format_count(val):
    """Formats whole numbers with commas (e.g., 19,290)"""
    return f"{int(val):,}" if val is not None else "0"


def format_percentage(val):
    """Formats percentages to 2 decimal places with a % symbol"""
    return f"{float(val):.2f}%" if val is not None else "0.00%"


def format_metric(val):
    """Formats averages to 2 decimal places"""
    return f"{float(val):.2f}" if val is not None else "N/A"


def get_analysis_data():
    """Queries PostgreSQL via SQLAlchemy ORM and returns formatted metrics for the dashboard."""
    session = SessionLocal()
    try:
        # Question 1: Fall 2026 Applicants Count
        q1_stmt = (
            select(func.count())
            .select_from(Applicant)
            .where(Applicant.term.ilike('%Fall 2026%'))
        )
        q1_result = session.scalar(q1_stmt)

        # Question 4: Average GPA - American Fall 2026
        q4_stmt = (
            select(func.avg(Applicant.gpa))
            .where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    Applicant.us_or_international.ilike('American')
                )
            )
        )
        q4_result = session.scalar(q4_stmt)

        # Question 5: Percentage Fall 2025 Acceptances
        accepted_case = case((Applicant.status.ilike('%Accept%'), 1), else_=0)
        q5_stmt = (
            select(
                (func.sum(accepted_case) * 100.0) / func.nullif(func.count(Applicant.p_id), 0)
            )
            .where(Applicant.term.ilike('%Fall 2025%'))
        )
        q5_result = session.scalar(q5_stmt)

        # Question 8: 4 Universities - PhD CS Acceptances Fall 2026 (Original Fields)
        q8_stmt = (
            select(func.count())
            .select_from(Applicant)
            .where(
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
        )
        q8_result = session.scalar(q8_stmt)

        # Question 9: 4 Universities - PhD CS Acceptances Fall 2026 (LLM Fields)
        q9_stmt = (
            select(func.count())
            .select_from(Applicant)
            .where(
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
        )
        q9_result = session.scalar(q9_stmt)

        diff = (q9_result or 0) - (q8_result or 0)
        sign = "+" if diff > 0 else ""

        # Custom Question 1: Average GPA by Admission Status (Fall 2026 PhDs)
        normalized_status = case(
            (Applicant.status.ilike('%Accept%'), 'Accepted'),
            (Applicant.status.ilike('%Reject%'), 'Rejected'),
            (Applicant.status.ilike('%Wait%'), 'Waitlisted'),
            else_='Other'
        ).label('clean_status')

        cq1_stmt = (
            select(
                normalized_status,
                func.avg(Applicant.gpa).label('avg_gpa'),
                func.count().label('total_applicants')
            )
            .where(
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
            )
            .group_by(normalized_status)
            .order_by(desc('avg_gpa'))
        )
        
        cq1_results = session.execute(cq1_stmt).all()
        gpa_by_status = [
            {
                "status": row.clean_status,
                "avg_gpa": format_metric(row.avg_gpa),
                "count": format_count(row.total_applicants)
            }
            for row in cq1_results
        ]

        # Total record count for general dashboard metric
        total_records_stmt = select(func.count()).select_from(Applicant)
        total_records = session.scalar(total_records_stmt)

        return {
            "total_records": format_count(total_records),
            "fall_2026_count": format_count(q1_result),
            "american_fall_2026_gpa": format_metric(q4_result),
            "fall_2025_acceptance_pct": format_percentage(q5_result),
            "q8_original_count": format_count(q8_result),
            "q9_llm_count": format_count(q9_result),
            "q8_q9_difference": f"{sign}{diff}",
            "gpa_by_status": gpa_by_status
        }

    except Exception as e:
        print(f"[ORM ERROR] Error retrieving analysis data: {e}")
        return {
            "total_records": "0",
            "fall_2026_count": "0",
            "american_fall_2026_gpa": "N/A",
            "fall_2025_acceptance_pct": "0.00%",
            "q8_original_count": "0",
            "q9_llm_count": "0",
            "q8_q9_difference": "0",
            "gpa_by_status": []
        }
    finally:
        session.close()


if __name__ == "__main__": # pragma: no cover
    # Allows testing the queries directly via CLI
    data = get_analysis_data()
    print("Analysis Data Output:")
    for k, v in data.items():
        print(f"  {k}: {v}")