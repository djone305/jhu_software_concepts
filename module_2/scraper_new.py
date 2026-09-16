import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Set
import requests
from bs4 import BeautifulSoup


def scrape(
    target_count: int = 30000,
    start_page: int = 1,
    seen_urls: Optional[Set[str]] = None,
) -> tuple[List[Dict[str, Optional[str]]], Set[str], int]:
    """Scrapes GradCafe pages until target_count unique entries are collected.

    Supports resuming from a given start page and existing URL set.
    """
    if seen_urls is None:
        seen_urls = set()

    results: List[Dict[str, Optional[str]]] = []
    current_page = start_page

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print(
        f"Starting scrape from page {current_page}. Target: {target_count} unique items."
    )

    try:
        while len(results) < target_count:
            url = f"https://www.thegradcafe.com/survey?page={current_page}"
            print(
                f"Fetching Page {current_page}... (Total unique collected: {len(results)})"
            )

            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    print(
                        f"Page {current_page} returned status {response.status_code}. Retrying in 5 seconds..."
                    )
                    time.sleep(5)
                    continue
            except requests.RequestException as e:
                print(f"Network error on page {current_page}: {e}. Retrying...")
                time.sleep(5)
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            tbody = soup.find("tbody", class_=re.compile(r"tw-divide-y"))

            if not tbody:
                print(
                    f"No results table found on page {current_page}. Ending crawl."
                )
                break

            rows = tbody.find_all("tr", recursive=False)
            if not rows:
                print(f"Empty page encountered at page {current_page}.")
                break

            page_entries_found = 0
            i = 0
            while i < len(rows):
                main_row = rows[i]
                cols = main_row.find_all("td", recursive=False)

                if len(cols) < 5:
                    i += 1
                    continue

                # URL Link & Deduplication check
                link_tag = cols[4].find("a", href=True)
                entry_url = (
                    f"https://www.thegradcafe.com{link_tag['href']}"
                    if link_tag
                    else None
                )

                if entry_url and entry_url in seen_urls:
                    # Skip duplicate record
                    i += 1
                    continue

                # Primary Row Data
                university = cols[0].get_text(strip=True)

                prog_container = cols[1].find(
                    "div", class_=re.compile(r"tw-text-gray-900")
                )
                spans = (
                    prog_container.find_all("span") if prog_container else []
                )
                program_name = (
                    spans[0].get_text(strip=True) if len(spans) > 0 else None
                )
                degree = (
                    spans[1].get_text(strip=True) if len(spans) > 1 else None
                )

                date_added = cols[2].get_text(strip=True)
                status_text = cols[3].get_text(strip=True)

                accepted_date, rejected_date = None, None
                if "Accepted on" in status_text:
                    accepted_date = status_text.split("Accepted on")[-1].strip()
                elif "Rejected on" in status_text:
                    rejected_date = status_text.split("Rejected on")[-1].strip()

                # Sub-row Details
                term, student_status = None, None
                gpa, gre, gre_v, gre_aw = None, None, None, None
                comments = None

                j = i + 1
                while j < len(rows):
                    sub_row = rows[j]
                    if len(sub_row.find_all("td", recursive=False)) >= 5:
                        break

                    badges = sub_row.find_all(
                        "div", class_=re.compile(r"tw-rounded-md")
                    )
                    for badge in badges:
                        text = badge.get_text(strip=True)
                        if re.search(
                            r"\b(Fall|Spring|Summer|Winter)\s+\d{4}\b",
                            text,
                            re.IGNORECASE,
                        ):
                            term = text
                        elif text in ["American", "International"]:
                            student_status = text
                        elif text.startswith("GPA"):
                            gpa = text.replace("GPA", "").strip()
                        elif text.startswith("GRE V"):
                            gre_v = text.replace("GRE V", "").strip()
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

                # Register record
                if entry_url:
                    seen_urls.add(entry_url)

                results.append(
                    {
                        "University": university,
                        "Program Name": program_name,
                        "Masters or PhD": degree,
                        "Date of Information Added to Grad Cafe": date_added,
                        "Applicant Status": status_text,
                        "Accepted: Acceptance Date": accepted_date,
                        "Rejected: Rejection Date": rejected_date,
                        "URL link to applicant entry": entry_url,
                        "Semester and Year of Program Start": term,
                        "International / American Student": student_status,
                        "GPA": gpa,
                        "GRE Score": gre,
                        "GRE V Score": gre_v,
                        "GRE AW": gre_aw,
                        "Comments": comments,
                    }
                )

                page_entries_found += 1
                if len(results) >= target_count:
                    break

            current_page += 1
            # Rate limiting delay to respect server resources
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nScrape manually interrupted by user.")

    return results, seen_urls, current_page


def save_data(
    data: List[Dict[str, Any]],
    seen_urls: Set[str],
    next_page: int,
    data_filename: str = "gradcafe_results.json",
    state_filename: str = "scraper_state.json",
) -> None:
    """Saves dataset along with execution state (last page, seen URLs) to allow seamless resumption."""
    # 1. Load existing JSON data if available to combine runs
    existing_data = []
    if os.path.exists(data_filename):
        with open(data_filename, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []

    combined_data = existing_data + data

    # 2. Write updated dataset
    with open(data_filename, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=4, ensure_ascii=False)

    # 3. Save current state
    state = {"next_page": next_page, "seen_urls": list(seen_urls)}
    with open(state_filename, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

    print(
        f"Saved {len(combined_data)} total items to '{data_filename}'. Resuming page saved as {next_page}."
    )


def load_state(
    state_filename: str = "scraper_state.json",
) -> tuple[int, Set[str]]:
    """Loads execution state if file exists, else defaults to fresh start."""
    if os.path.exists(state_filename):
        with open(state_filename, "r", encoding="utf-8") as f:
            try:
                state = json.load(f)
                return state.get("next_page", 1), set(
                    state.get("seen_urls", [])
                )
            except json.JSONDecodeError:
                pass
    return 1, set()


# --- Execution Entry Point ---
if __name__ == "__main__":
    TARGET_RECORDS = 30000
    DATA_FILE = "gradcafe_30k_results.json"
    STATE_FILE = "scraper_state.json"

    # Resume from previous run if state exists
    start_page, seen_urls = load_state(STATE_FILE)

    remaining_needed = TARGET_RECORDS - len(seen_urls)
    if remaining_needed <= 0:
        print(f"Target of {TARGET_RECORDS} records already reached.")
    else:
        print(f"Loaded existing state. Unique records so far: {len(seen_urls)}")
        new_data, updated_urls, next_page = scrape(
            target_count=remaining_needed,
            start_page=start_page,
            seen_urls=seen_urls,
        )

        save_data(
            data=new_data,
            seen_urls=updated_urls,
            next_page=next_page,
            data_filename=DATA_FILE,
            state_filename=STATE_FILE,
        )