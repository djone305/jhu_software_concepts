import hashlib
import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import requests
from tqdm import tqdm

# ============================================================
# Configuration
# ============================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.join(SCRIPT_DIR, "applicant_data.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "llm_extend_applicant_data_clean.json")

API_URL = "http://127.0.0.1:8000/standardize"

CHECKPOINT_EVERY = 25
REQUEST_TIMEOUT = 120

# Optimized for a laptop with 12GB VRAM (keeps GPU fed without OOM)
MAX_WORKERS = 4 


# ============================================================
# Safe JSON saving
# ============================================================

def save_json_atomic(path: str, data: List[Dict[str, Any]]) -> None:
    """Safely save JSON by writing to a temporary file first, then replacing."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        prefix=os.path.basename(path) + ".",
        suffix=".tmp",
        dir=directory,
        text=True,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, path)

    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


# ============================================================
# JSON loading
# ============================================================

def load_json(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list.")

    return data


# ============================================================
# Stable record ID
# ============================================================

def make_source_id(record: Dict[str, Any]) -> str:
    """Create a stable ID for a GradCafe record."""
    url = str(
        record.get("URL link to applicant entry") 
        or record.get("url") 
        or ""
    ).strip()

    if url:
        return "url:" + url

    parts = [
        str(record.get("University", "")).strip(),
        str(record.get("Program Name", "")).strip(),
        str(record.get("Masters or PhD", "")).strip(),
        str(record.get("Semester and Year of Program Start", "")).strip(),
        str(record.get("Date of Information Added to Grad Cafe", "")).strip(),
        str(record.get("Applicant Status", "")).strip(),
    ]

    raw = "|".join(parts)
    return "record:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ============================================================
# Database ID
# ============================================================

def make_p_id(source_id: str) -> int:
    """Create a deterministic positive PostgreSQL INTEGER ID."""
    digest = hashlib.sha256(source_id.encode("utf-8")).digest()
    value = int.from_bytes(digest[:4], "big") & 0x7FFFFFFF
    return value or 1


# ============================================================
# Field helpers
# ============================================================

def get_program(record: Dict[str, Any]) -> Any:
    return record.get("Program Name") or record.get("program")

def get_university(record: Dict[str, Any]) -> Any:
    return record.get("University") or record.get("university")


# ============================================================
# Convert LLM response & Create Fallbacks
# ============================================================

def convert_record(
    original: Dict[str, Any],
    llm_result: Dict[str, Any],
    source_id: str,
) -> Dict[str, Any]:

    llm_program = (
        llm_result.get("llm_generated_program") or 
        llm_result.get("llm-generated-program")
    )
    llm_university = (
        llm_result.get("llm_generated_university") or 
        llm_result.get("llm-generated-university")
    )

    return {
        "p_id": make_p_id(source_id),
        "program": get_program(original),
        "comments": original.get("Comments"),
        "date_added": original.get("Date of Information Added to Grad Cafe"),
        "url": original.get("URL link to applicant entry"),
        "status": original.get("Applicant Status"),
        "term": original.get("Semester and Year of Program Start"),
        "us_or_international": original.get("International / American Student"),
        "gpa": original.get("GPA"),
        "gre": original.get("GRE Score"),
        "gre_v": original.get("GRE V Score"),
        "gre_aw": original.get("GRE AW"),
        "degree": original.get("Masters or PhD"),
        "llm_generated_program": llm_program,
        "llm_generated_university": llm_university,
        "_source_id": source_id,
        "_llm_status": "success",
    }


def make_fallback_record(record: Dict[str, Any], source_id: str) -> Dict[str, Any]:
    """Generates a fallback record if the LLM request fails."""
    return {
        "p_id": make_p_id(source_id),
        "program": get_program(record),
        "comments": record.get("Comments"),
        "date_added": record.get("Date of Information Added to Grad Cafe"),
        "url": record.get("URL link to applicant entry"),
        "status": record.get("Applicant Status"),
        "term": record.get("Semester and Year of Program Start"),
        "us_or_international": record.get("International / American Student"),
        "gpa": record.get("GPA"),
        "gre": record.get("GRE Score"),
        "gre_v": record.get("GRE V Score"),
        "gre_aw": record.get("GRE AW"),
        "degree": record.get("Masters or PhD"),
        "llm_generated_program": None,
        "llm_generated_university": None,
        "_source_id": source_id,
        "_llm_status": "failed",
    }


# ============================================================
# Send one record to the LLM
# ============================================================

def process_record(
    session: requests.Session,
    record: Dict[str, Any],
    source_id: str,
) -> Dict[str, Any]:

    payload = {
        "program": get_program(record),
        "university": get_university(record),
    }

    response = session.post(
        API_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()

    # --------------------------------------------------------
    # Accept several possible response formats.
    # --------------------------------------------------------
    if isinstance(result, dict):
        if "llm_generated_program" in result or "llm-generated-program" in result:
            llm_result = result
        elif "rows" in result and isinstance(result["rows"], list) and result["rows"]:
            llm_result = result["rows"][0]
        else:
            llm_result = result
    elif isinstance(result, list) and result:
        llm_result = result[0]
    else:
        raise ValueError("Unexpected LLM response format.")

    if not isinstance(llm_result, dict):
        raise ValueError("LLM response did not contain a JSON object.")

    return convert_record(original=record, llm_result=llm_result, source_id=source_id)


def worker_task(session: requests.Session, record: Dict[str, Any]) -> tuple[bool, Dict[str, Any], str]:
    """Function executed by each parallel thread."""
    source_id = make_source_id(record)
    try:
        cleaned_record = process_record(session, record, source_id)
        return True, cleaned_record, source_id
    except Exception as e:
        fallback = make_fallback_record(record, source_id)
        return False, fallback, source_id


# ============================================================
# Main
# ============================================================

def main() -> None:

    print("=" * 60)
    print(f"GradCafe LLM Data Cleaner (Parallel: {MAX_WORKERS} Workers)")
    print("=" * 60)

    print("\nLoading raw applicant data...")
    records = load_json(INPUT_FILE)
    print(f"Raw records: {len(records):,}")

    processed_records = load_json(OUTPUT_FILE)
    print(f"Existing cleaned records: {len(processed_records):,}")

    # Map existing records by _source_id for O(1) dictionary updates
    processed_map: Dict[str, Dict[str, Any]] = {
        r["_source_id"]: r for r in processed_records if "_source_id" in r
    }

    # Identify source_ids that are already successfully processed
    processed_ids = {
        sid for sid, r in processed_map.items() if r.get("_llm_status") == "success"
    }

    print(f"Already successfully processed: {len(processed_ids):,}")

    # Filter out records that are already successful
    records_to_process = [r for r in records if make_source_id(r) not in processed_ids]

    print(f"Records remaining to process: {len(records_to_process):,}")
    print(f"LLM API: {API_URL}")
    print("\nStarting cleaning...\n")

    new_count = 0
    failed_count = 0

    # Share a single Session to reuse HTTP connections across threads
    session = requests.Session()

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            
            # Queue up all remaining tasks
            futures = {
                executor.submit(worker_task, session, record): record 
                for record in records_to_process
            }

            # As tasks finish (in whatever order they complete), process the results
            for future in tqdm(as_completed(futures), total=len(futures), desc="Cleaning"):
                success, final_record, source_id = future.result()
                
                # Update map in O(1) time
                processed_map[source_id] = final_record
                
                if success:
                    processed_ids.add(source_id)
                    new_count += 1
                else:
                    failed_count += 1

                # ------------------------------------------------
                # Checkpoint
                # ------------------------------------------------
                total_this_run = new_count + failed_count
                if total_this_run > 0 and total_this_run % CHECKPOINT_EVERY == 0:
                    save_json_atomic(OUTPUT_FILE, list(processed_map.values()))
                    # Use tqdm.write inside the loop so the progress bar doesn't break
                    tqdm.write(f"Checkpoint saved: {len(processed_map):,} total records")

    # --------------------------------------------------------
    # Ctrl+C
    # --------------------------------------------------------
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("INTERRUPTED BY USER")
        print("=" * 60)
        print("Saving current progress...")
        save_json_atomic(OUTPUT_FILE, list(processed_map.values()))
        print(f"Saved {len(processed_map):,} records.\nRun clean.py again to continue.")
        return

    # --------------------------------------------------------
    # Unexpected error
    # --------------------------------------------------------
    except Exception:
        print("\nUnexpected error occurred.")
        print("Saving current progress before exiting...")
        save_json_atomic(OUTPUT_FILE, list(processed_map.values()))
        raise

    # --------------------------------------------------------
    # Final save
    # --------------------------------------------------------
    save_json_atomic(OUTPUT_FILE, list(processed_map.values()))

    print("\n" + "=" * 60)
    print("CLEANING COMPLETE")
    print("=" * 60)
    print(f"Total records in output: {len(processed_map):,}")
    print(f"Newly processed this run: {new_count:,}")
    print(f"LLM failures this run: {failed_count:,}")
    print("\nOutput file:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()