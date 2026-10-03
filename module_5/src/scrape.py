import argparse
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "applicant_data.json")
STATE_FILE = os.path.join(SCRIPT_DIR, "scraper_state.json")
TARGET_RECORDS = 52000

# Query partitioning to bypass GradCafe's pagination depth cap
SEARCH_TERMS = [str(year) for year in range(2026, 2027)] + [
    chr(c) for c in range(ord("a"), ord("z") + 1)
]


def get_record_id(
    url: Optional[str],
    university: str,
    program_name: Optional[str],
    date_added: str,
    status_text: str,
) -> str:
    """
    Generates a unique identifier using URL or a composite fallback signature.

    Args:
        url (str, optional): The direct URL link to the applicant entry.
        university (str): The name of the university.
        program_name (str, optional): The graduate program name.
        date_added (str): The date the record was posted to GradCafe.
        status_text (str): The raw text of the admission status.

    Returns:
        str: A unique identifier string for the database to prevent duplicates.
    """
    if url:
        return url
    return f"{university}|{program_name or ''}|{date_added}|{status_text}"


def get_http_session() -> requests.Session:
    """
    Initializes an HTTP session with retry backoff and browser headers.

    Returns:
        requests.Session: A configured requests session object resilient to rate limits.
    """
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
    )
    return session


def parse_status_dates(status_text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extracts status dates from the main row status string.

    Args:
        status_text (str): The raw text string containing the decision and date.

    Returns:
        tuple: A 3-tuple containing (accepted_date, rejected_date, waitlist_date).
               Values are strings if found, otherwise None.
    """
    accepted, rejected, waitlisted = None, None, None
    if "Accepted on" in status_text:
        accepted = status_text.split("Accepted on")[-1].strip()
    elif "Rejected on" in status_text:
        rejected = status_text.split("Rejected on")[-1].strip()
    elif "Waitlisted on" in status_text:
        waitlisted = status_text.split("Waitlisted on")[-1].strip()
    return accepted, rejected, waitlisted


def load_existing_data(
    data_filename: str = DATA_FILE, state_filename: str = STATE_FILE
) -> tuple[List[Dict[str, Any]], Set[str], int, int]:
    """
    Loads saved dataset and scraper state synchronously from disk.

    Args:
        data_filename (str, optional): Path to the JSON data file. Defaults to DATA_FILE.
        state_filename (str, optional): Path to the JSON state tracker. Defaults to STATE_FILE.

    Returns:
        tuple: Contains (scraped_data list, seen_ids set, start_term_idx int, start_page int).
    """
    scraped_data: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    start_term_idx: int = 0
    start_page: int = 1

    if os.path.exists(data_filename):
        try:
            with open(data_filename, "r", encoding="utf-8") as f:
                scraped_data = json.load(f)
                for item in scraped_data:
                    rec_id = get_record_id(
                        item.get("URL link to applicant entry"),
                        item.get("University", ""),
                        item.get("Program Name"),
                        item.get("Date of Information Added to Grad Cafe", ""),
                        item.get("Applicant Status", ""),
                    )
                    seen_ids.add(rec_id)
        except (json.JSONDecodeError, OSError) as e:  
            print(f"Warning: Failed to parse '{data_filename}' ({e}). Starting fresh array.")

    if os.path.exists(state_filename):
        try:
            with open(state_filename, "r", encoding="utf-8") as f:
                state = json.load(f)
                start_term_idx = state.get("term_idx", 0)
                start_page = state.get("page_num", 1)
                seen_ids.update(state.get("seen_ids", []))
        except (json.JSONDecodeError, OSError):  
            pass

    return scraped_data, seen_ids, start_term_idx, start_page


def save_data(
    all_data: List[Dict[str, Any]],
    seen_ids: Set[str],
    term_idx: int,
    page_num: int,
    data_filename: str = DATA_FILE,
    state_filename: str = STATE_FILE,
) -> None:
    """
    Atomically updates the data file and scraper resume state on disk.

    Args:
        all_data (list): The complete list of applicant record dictionaries.
        seen_ids (set): The set of unique record IDs already processed.
        term_idx (int): The current index of the SEARCH_TERMS list.
        page_num (int): The current pagination index for the search term.
        data_filename (str, optional): Path to output JSON. Defaults to DATA_FILE.
        state_filename (str, optional): Path to state JSON. Defaults to STATE_FILE.

    Returns:
        None
    """
    temp_data_file = f"{data_filename}.tmp"
    temp_state_file = f"{state_filename}.tmp"

    try:
        with open(temp_data_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        os.replace(temp_data_file, data_filename)

        state = {
            "term_idx": term_idx,
            "page_num": page_num,
            "seen_ids": list(seen_ids),
        }
        with open(temp_state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(temp_state_file, state_filename)

        current_term = (
            SEARCH_TERMS[term_idx] if term_idx < len(SEARCH_TERMS) else "Completed"
        )
        print(
            f" [DISK SAVED] Total Records: {len(all_data):,} | "
            f"Partition Index: {term_idx} ('{current_term}') | Page: {page_num}"
        )
    except Exception as e: 
        print(f"Error saving data: {e}")


def scrape(
    target_count: int = TARGET_RECORDS,
    start_term_idx: int = 0,
    start_page: int = 1,
    existing_data: Optional[List[Dict[str, Any]]] = None,
    seen_ids: Optional[Set[str]] = None,
) -> tuple[List[Dict[str, Any]], Set[str], int, int]:
    """
    Iterates through search partitions to harvest applicant entries up to a target count.

    Args:
        target_count (int, optional): The total number of records to stop at. Defaults to TARGET_RECORDS.
        start_term_idx (int, optional): The search term index to begin with. Defaults to 0.
        start_page (int, optional): The GradCafe page number to begin with. Defaults to 1.
        existing_data (list, optional): Pre-loaded records to append to. Defaults to None.
        seen_ids (set, optional): Pre-loaded IDs for deduplication. Defaults to None.

    Returns:
        tuple: A 4-tuple containing the final lists/states: (final_data, seen_ids, term_idx, page_num).
    """
    all_data = existing_data if existing_data is not None else []
    seen_ids = seen_ids if seen_ids is not None else set()
    session = get_http_session()

    term_idx = start_term_idx
    page_num = start_page

    print(f"Resuming Scrape | Current Records: {len(all_data):,}/{target_count:,}")

    try:
        while term_idx < len(SEARCH_TERMS) and len(all_data) < target_count:
            term = SEARCH_TERMS[term_idx]
            consecutive_empty_pages = 0
            print(f"\n=== Partition [{term_idx + 1}/{len(SEARCH_TERMS)}]: Querying '{term}' ===")

            while len(all_data) < target_count:
                url = (
                    f"https://www.thegradcafe.com/survey?"
                    f"q={requests.utils.quote(term)}&page={page_num}"
                )
                print(
                    f"Query: '{term:<10}' | Page: {page_num:<3} | "
                    f"Running Total: {len(all_data):,}/{target_count:,} records"
                )

                try:
                    response = session.get(url, timeout=12)
                    if response.status_code != 200:
                        print(f"Page {page_num} returned HTTP {response.status_code}. Skipping...")
                        page_num += 1
                        continue
                except requests.RequestException as e:  
                    print(f"Network error on page {page_num}: {e}. Skipping...")
                    page_num += 1
                    continue

                soup = BeautifulSoup(response.content, "html.parser")
                tbody = soup.find("tbody", class_=re.compile(r"tw-divide-y"))

                if not tbody:
                    print(f"No results container on page {page_num}. Switching term.")
                    break

                rows = tbody.find_all("tr", recursive=False)
                if not rows:
                    print(f"Empty row set on page {page_num}. Switching term.")
                    break

                records_added_this_page = 0
                i = 0

                while i < len(rows):
                    main_row = rows[i]
                    cols = main_row.find_all("td", recursive=False)

                    if len(cols) < 5:
                        i += 1
                        continue

                    university = cols[0].get_text(strip=True)
                    prog_container = cols[1].find("div", class_=re.compile(r"tw-text-gray-900"))
                    spans = prog_container.find_all("span") if prog_container else []
                    program_name = spans[0].get_text(strip=True) if len(spans) > 0 else None
                    degree = spans[1].get_text(strip=True) if len(spans) > 1 else None

                    date_added = cols[2].get_text(strip=True)
                    status_text = cols[3].get_text(strip=True)

                    link_tag = cols[4].find("a", href=True)
                    entry_url = (
                        f"https://www.thegradcafe.com{link_tag['href']}"
                        if link_tag
                        else None
                    )

                    rec_id = get_record_id(
                        entry_url, university, program_name, date_added, status_text
                    )

                    if rec_id in seen_ids:
                        i += 1
                        while i < len(rows) and len(rows[i].find_all("td", recursive=False)) < 5:
                            i += 1
                        continue

                    accepted_date, rejected_date, waitlist_date = parse_status_dates(status_text)
                    term_season, student_status = None, None
                    gpa, gre, gre_v, gre_q, gre_aw = None, None, None, None, None
                    comments = None

                    j = i + 1
                    while j < len(rows):
                        sub_row = rows[j]
                        if len(sub_row.find_all("td", recursive=False)) >= 5:
                            break

                        badges = sub_row.find_all("div", class_=re.compile(r"tw-rounded-md"))
                        for badge in badges:
                            text = badge.get_text(strip=True)
                            if re.search(r"\b(Fall|Spring|Summer|Winter)\s+\d{4}\b", text, re.I):
                                term_season = text
                            elif text in ["American", "International"]:
                                student_status = text
                            elif text.startswith("GPA"):
                                gpa = text.replace("GPA", "").strip()
                            elif text.startswith("GRE V"):
                                gre_v = text.replace("GRE V", "").strip()
                            elif text.startswith("GRE Q"):
                                gre_q = text.replace("GRE Q", "").strip()
                            elif text.startswith("GRE AW"):
                                gre_aw = text.replace("GRE AW", "").strip()
                            elif text.startswith("GRE"):
                                gre = text.replace("GRE", "").strip()

                        comment_p = sub_row.find(
                            "p", class_=re.compile(r"tw-text-gray-500.*tw-text-sm")
                        )
                        if comment_p:
                            comments = comment_p.get_text(strip=True)

                        j += 1

                    i = j
                    seen_ids.add(rec_id)

                    all_data.append(
                        {
                            "University": university,
                            "Program Name": program_name,
                            "Masters or PhD": degree,
                            "Date of Information Added to Grad Cafe": date_added,
                            "Applicant Status": status_text,
                            "Accepted: Acceptance Date": accepted_date,
                            "Rejected: Rejection Date": rejected_date,
                            "Waitlisted Date": waitlist_date,
                            "URL link to applicant entry": entry_url,
                            "Semester and Year of Program Start": term_season,
                            "International / American Student": student_status,
                            "GPA": gpa,
                            "GRE Score": gre,
                            "GRE V Score": gre_v,
                            "GRE Q Score": gre_q,
                            "GRE AW": gre_aw,
                            "Comments": comments,
                        }
                    )
                    records_added_this_page += 1

                    if len(all_data) >= target_count:
                        break

                if records_added_this_page == 0:
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 3:
                        print(f"Partition '{term}' exhausted or duplicate capped. Switching term.")
                        break
                else:
                    consecutive_empty_pages = 0

                page_num += 1

                if page_num % 5 == 0 or len(all_data) >= target_count:
                    save_data(all_data, seen_ids, term_idx, page_num)

                time.sleep(1)

            term_idx += 1
            page_num = 1
            save_data(all_data, seen_ids, term_idx, page_num)

    except KeyboardInterrupt: 
        print("\nProcess manually interrupted! Flushing current state to disk...")
        save_data(all_data, seen_ids, term_idx, page_num)

    return all_data, seen_ids, term_idx, page_num


def run_scrape(record_limit: int = 10) -> List[Dict[str, Any]]:
    """
    Programmatic entry point for Flask apps to trigger scraping of N new records.

    Args:
        record_limit (int, optional): The exact number of new records to fetch. Defaults to 10.

    Returns:
        list: A list containing only the newly scraped applicant dictionaries.
    """
    existing_data, seen_ids, start_term_idx, start_page = load_existing_data()
    initial_count = len(existing_data)
    target_count = initial_count + record_limit

    final_data, updated_ids, end_term, end_page = scrape(
        target_count=target_count,
        start_term_idx=start_term_idx,
        start_page=start_page,
        existing_data=existing_data,
        seen_ids=seen_ids,
    )
    save_data(final_data, updated_ids, end_term, end_page)

    # Return newly scraped elements
    return final_data[initial_count:]


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="GradCafe Web Scraper")
    parser.add_argument("--limit", type=int, default=TARGET_RECORDS, help="Total target records or limit to pull")
    args = parser.parse_args()

    existing_data, seen_ids, start_term_idx, start_page = load_existing_data()

    if len(existing_data) >= args.limit and args.limit == TARGET_RECORDS:
        print(f"Target of {args.limit:,} records already achieved in '{DATA_FILE}'!")
    else:
        target = args.limit if args.limit != TARGET_RECORDS else args.limit
        final_data, updated_ids, end_term, end_page = scrape(
            target_count=target,
            start_term_idx=start_term_idx,
            start_page=start_page,
            existing_data=existing_data,
            seen_ids=seen_ids,
        )
        save_data(final_data, updated_ids, end_term, end_page)