import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, select, func, case, or_, and_, desc, Float, cast
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

if not DB_PASSWORD:
    raise ValueError("Missing database password! Set the DB_PASSWORD environment variable.")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Formatting Helpers ---
def format_count(val):
    """
    Formats a numeric value as a comma-separated integer string.

    Args:
        val (int or float or None): The raw numeric value.

    Returns:
        str: The formatted integer string, or "0" if the value is None.
    """
    return f"{int(val):,}" if val is not None else "0"


def format_percentage(val):
    """
    Formats a numeric value as a two-decimal percentage string.

    Args:
        val (float or None): The raw decimal percentage.

    Returns:
        str: The formatted percentage string (e.g., "52.51%"), or "0.00%" if None.
    """
    return f"{float(val):.2f}%" if val is not None else "0.00%"


def format_metric(val):
    """
    Formats a numeric value as a two-decimal floating point string.

    Args:
        val (float or None): The raw numeric metric (e.g., GPA).

    Returns:
        str: The formatted float string, or "N/A" if the value is None.
    """
    return f"{float(val):.2f}" if val is not None else "N/A"


def run_orm_queries():
    """
    Executes a suite of SQLAlchemy ORM queries to extract analytical insights 
    from the graduate admissions database, printing formatted results to standard output.

    Queries executed include:
        - Fall 2026 total applicant count.
        - Average GPA of American Fall 2026 applicants.
        - Acceptance rate for Fall 2025.
        - PhD Computer Science acceptances (original vs LLM-generated comparison).
        - Average GPA grouped by admission status.

    Returns:
        None
    """
    session = SessionLocal()
    try:
        print("=" * 50)
        print(" SQLAlchemy ORM Query Analysis Results")
        print("=" * 50)

        # ---------------------------------------------------------
        # Question 1: Fall 2026 Applicants Count
        # ---------------------------------------------------------
        print("\n--- Question 1 ---")
        print("Question: How many entries in your database are from applicants who applied for Fall 2026?")
        q1_stmt = (
            select(func.count(Applicant.p_id))
            .where(Applicant.term.ilike('%Fall 2026%'))
        )
        q1_result = session.scalar(q1_stmt)
        print(f"Fall 2026 applicant count: {format_count(q1_result)}")

        # ---------------------------------------------------------
        # Question 4: Average GPA - American Fall 2026
        # ---------------------------------------------------------
        print("\n--- Question 4 ---")
        print("Question: What is the average GPA of American applicants who applied for Fall 2026?")
        q4_stmt = (
            select(func.avg(Applicant.gpa))
            .where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    Applicant.us_or_international.ilike('%American%'),
                    Applicant.gpa.is_not(None)
                )
            )
        )
        q4_result = session.scalar(q4_stmt)
        print(f"Average GPA of American applicants (Fall 2026): {format_metric(q4_result)}")

        # ---------------------------------------------------------
        # Question 5: Percentage Fall 2025 Acceptances
        # ---------------------------------------------------------
        print("\n--- Question 5 ---")
        print("Question: What percentage of Fall 2025 entries are acceptances?")
        
        total_fall_2025 = func.nullif(func.count(Applicant.p_id), 0)
        accepted_count = func.sum(
            case((Applicant.status.ilike('%Accept%'), 1), else_=0)
        )
        
        q5_stmt = (
            select(
                cast(accepted_count, Float) * 100.0 / cast(total_fall_2025, Float)
            )
            .where(Applicant.term.ilike('%Fall 2025%'))
        )
        q5_result = session.scalar(q5_stmt)
        print(f"Fall 2025 acceptance percentage: {format_percentage(q5_result)}")

        # ---------------------------------------------------------
        # Question 8: 4 Universities - PhD CS Acceptances Fall 2026 (Original Fields)
        # ---------------------------------------------------------
        print("\n--- Question 8 ---")
        print("Question: How many Fall 2026 entries are acceptances for PhD Computer Science at Georgetown, MIT, Stanford, or CMU (original fields)?")
        
        target_unis = ['%Georgetown%', '%Massachusetts Institute of Technology%', '%MIT%', '%Stanford%', '%Carnegie Mellon%', '%CMU%']
        uni_conditions_q8 = [Applicant.program.ilike(pattern) for pattern in target_unis]

        q8_stmt = (
            select(func.count(Applicant.p_id))
            .where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    Applicant.status.ilike('%Accept%'),
                    or_(
                        Applicant.degree.ilike('%PhD%'),
                        Applicant.degree.ilike('%Ph.D%')
                    ),
                    Applicant.program.ilike('%Computer Science%'),
                    or_(*uni_conditions_q8)
                )
            )
        )
        q8_result = session.scalar(q8_stmt)
        print(f"Original-field count: {format_count(q8_result)}")

        # ---------------------------------------------------------
        # Question 9: 4 Universities - PhD CS Acceptances Fall 2026 (LLM Fields)
        # ---------------------------------------------------------
        print("\n--- Question 9 ---")
        print("Question: Repeat Question 8 using LLM-generated university and program fields.")
        
        uni_conditions_q9 = [Applicant.llm_generated_university.ilike(pattern) for pattern in target_unis]

        q9_stmt = (
            select(func.count(Applicant.p_id))
            .where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    Applicant.status.ilike('%Accept%'),
                    or_(
                        Applicant.degree.ilike('%PhD%'),
                        Applicant.degree.ilike('%Ph.D%')
                    ),
                    Applicant.llm_generated_program.ilike('%Computer Science%'),
                    or_(*uni_conditions_q9)
                )
            )
        )
        q9_result = session.scalar(q9_stmt)

        diff = (q9_result or 0) - (q8_result or 0)
        sign = "+" if diff > 0 else ""

        print(f"Original-field count: {format_count(q8_result)}")
        print(f"LLM-field count:      {format_count(q9_result)}")
        print(f"Difference:           {sign}{diff}")

        # ---------------------------------------------------------
        # Custom Question 1: Average GPA by Admission Status (Fall 2026 PhDs)
        # ---------------------------------------------------------
        print("\n--- Custom Question 1 ---")
        print("Question: What is the average GPA of Fall 2026 PhD applicants, grouped by admission status?")
        
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
                func.count(Applicant.p_id).label('total_applicants')
            )
            .where(
                and_(
                    Applicant.term.ilike('%Fall 2026%'),
                    or_(
                        Applicant.degree.ilike('%PhD%'),
                        Applicant.degree.ilike('%Ph.D%')
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

        for row in cq1_results:
            print(f"Status: {row.clean_status:<10} | Average GPA: {format_metric(row.avg_gpa)} | Count: {format_count(row.total_applicants)}")

        print("\n" + "=" * 50)

    finally:
        session.close()


if __name__ == "__main__":
    run_orm_queries()