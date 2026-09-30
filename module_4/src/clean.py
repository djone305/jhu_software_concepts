from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple
import requests

LLM_ENDPOINT = "http://127.0.0.1:8000/standardize"
MAX_WORKERS = 8


def worker_task(session: requests.Session, record: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """
    Sends a single record to the LLM endpoint for standardization.

    Args:
        session (requests.Session): The active requests session.
        record (dict): A dictionary representing a single raw applicant record.

    Returns:
        tuple: A 3-tuple containing:
            - bool: True if the request was successful, False otherwise.
            - dict: The standardized record if successful, or the original record if failed.
            - str: Error message or HTTP status if the request failed, else an empty string.
    """
    try:
        response = session.post(LLM_ENDPOINT, json=record, timeout=30)
        if response.status_code == 200:
            return True, response.json(), ""
        return False, record, f"HTTP {response.status_code}"
    except Exception as e:
        return False, record, str(e)


def clean_scraped_records(raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Called by Flask (app.py) to clean and standardize raw scraped records via the LLM API.
    
    Utilizes a ThreadPoolExecutor to process records concurrently.

    Args:
        raw_records (list): A list of dictionaries representing uncleaned applicant records.

    Returns:
        list: A list of dictionaries representing the cleaned and standardized records.
    """
    if not raw_records:
        return []

    cleaned_results = []
    session = requests.Session()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(worker_task, session, record): record
            for record in raw_records
        }
        for future in as_completed(futures):
            success, final_record, _ = future.result()
            cleaned_results.append(final_record)

    return cleaned_results