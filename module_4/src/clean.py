from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple
import requests

LLM_ENDPOINT = "http://127.0.0.1:8000/standardize"
MAX_WORKERS = 8


def worker_task(session: requests.Session, record: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """Sends a single record to the LLM endpoint for standardization."""
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