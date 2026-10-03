import logging
from typing import Any, Dict, List
from models import Applicant, SessionLocal

logger = logging.getLogger(__name__)

def safe_float(val: Any) -> float | None:
    """
    Safely casts a value to a float, returning None if invalid.

    Args:
        val (Any): The raw value to cast (string, int, float, etc.).

    Returns:
        float | None: The casted float value, or None if a ValueError or TypeError occurs.
    """
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None

def load_scraped_data_to_db(cleaned_records: List[Dict[str, Any]]) -> int:
    """
    Parses cleaned dictionaries, maps fields to the Applicant ORM model,
    and commits them to the PostgreSQL database in a single transaction.

    Args:
        cleaned_records (list): A list of dictionaries containing cleaned applicant data.

    Returns:
        int: The total number of records successfully inserted into the database.

    Raises:
        Exception: If the database transaction fails, triggering a rollback.
    """
    if not cleaned_records:
        return 0

    session = SessionLocal()
    inserted_count = 0

    try:
        for record in cleaned_records:
            applicant = Applicant(
                llm_generated_university=record.get("University"),
                program=record.get("Program Name"),
                degree=record.get("Masters or PhD"),
                status=record.get("Applicant Status"),
                url=record.get("URL link to applicant entry"),
                term=record.get("Semester and Year of Program Start"),
                us_or_international=record.get("International / American Student"),
                gpa=safe_float(record.get("GPA")),
                gre=safe_float(record.get("GRE Score")),
                gre_v=safe_float(record.get("GRE V Score")),
                gre_aw=safe_float(record.get("GRE AW")),
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