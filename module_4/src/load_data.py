import logging
from typing import Any, Dict, List
from models import Applicant, SessionLocal

logger = logging.getLogger(__name__)


def load_scraped_data_to_db(cleaned_records: List[Dict[str, Any]]) -> int:
    """
    Parses cleaned dictionaries, maps fields to the Applicant ORM model,
    and commits them to PostgreSQL. Returns inserted record count.
    """
    if not cleaned_records:
        return 0

    session = SessionLocal()
    inserted_count = 0

    try:
        for record in cleaned_records:
            applicant = Applicant(
                university=record.get("University"),
                program_name=record.get("Program Name"),
                degree_type=record.get("Masters or PhD"),
                date_added=record.get("Date of Information Added to Grad Cafe"),
                applicant_status=record.get("Applicant Status"),
                accepted_date=record.get("Accepted: Acceptance Date"),
                rejected_date=record.get("Rejected: Rejection Date"),
                waitlisted_date=record.get("Waitlisted Date"),
                url=record.get("URL link to applicant entry"),
                term_season=record.get("Semester and Year of Program Start"),
                student_status=record.get("International / American Student"),
                gpa=record.get("GPA"),
                gre=record.get("GRE Score"),
                gre_v=record.get("GRE V Score"),
                gre_q=record.get("GRE Q Score"),
                gre_aw=record.get("GRE AW"),
                comments=record.get("Comments"),
            )
            session.add(applicant)
            inserted_count += 1

        session.commit()
        logger.info(f"Successfully committed {inserted_count} records to database.")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to commit batch to database: {e}")
        raise e
    finally:
        session.close()

    return inserted_count