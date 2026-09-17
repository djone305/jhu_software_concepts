Name: Donnell Jones djone305
Course: Modern Software Concepts in Python
Semester: Fall '26
Module 2 Assignment: Web Scraping Due 9/13/2026

Skills: Python, Flask, Bootstrap, Git/GitHub


================================================================================
GRADCAFE DATA HARVESTING & GPU-ACCELERATED LLM CLEANING PIPELINE
================================================================================

PROJECT OVERVIEW
--------------------------------------------------------------------------------
This project implements an ethical, high-performance data ingestion and cleaning 
pipeline designed to harvest, parse, clean, and standardize large-scale academic 
applicant survey data (30,000+ records) from GradCafe. 

The architecture combines a lightweight HTTP scraping workflow with a local, 
GPU-accelerated LLM standardization layer.


WORKFLOW & TECHNICAL STACK
--------------------------------------------------------------------------------
- Workflow Type: Hybrid `requests` + `BeautifulSoup` + `urllib` (robots.txt parser) 
  workflow for scraping, augmented by a local LLM API (`Flask` + `llama-cpp-python`) 
  for data standardization.
- Selenium Usage: Selenium was NOT used. Target pages render static HTML tables 
  server-side, making lightweight HTTP requests via `requests` paired with 
  `BeautifulSoup` parsing and `urllib.robotparser` fully sufficient without 
  headless browser automation.
- Driver Setup: None required (no browser drivers like ChromeDriver or GeckoDriver).
- Data Cleaning Stack: `clean.py` interfaces with `app.py`, which runs a local 
  TinyLlama 1.1B GGUF model accelerated via CUDA on an NVIDIA RTX 5070 (32GB VRAM) 
  under Python 3.12 to programmatically standardize raw university and program strings.


DIRECTORY STRUCTURE
--------------------------------------------------------------------------------
module_2/
│
├── scraper.py                 # Scrapes GradCafe with robots.txt enforcement
├── clean.py                   # Data cleaning wrapper interfacing with local LLM
├── applicant_data.json        # Raw harvested dataset (~30,000 records)
├── scraper_state.json         # Checkpoint state file for resumability
├── llm_extend_applicant_data.json # Final cleaned and standardized dataset
├── requirements.txt           # Project Python dependencies
├── README.txt                 # Project documentation (this file)
│
├── llm_hosting/
│   ├── app.py                 # Local Flask inference server for GGUF models
│   └── requirements.txt       # Hosting dependencies
│
├── models/                    # Local storage for GGUF model weights (TinyLlama)
└── venv/                      # Python 3.12 virtual environment (CUDA-enabled)


APPROACH & ARCHITECTURE HIGHLIGHTS
--------------------------------------------------------------------------------
1. robots.txt Verification & Compliance:
   - Verification: The site's `robots.txt` file was programmatically checked and 
     parsed at startup using Python's built-in `urllib.robotparser.RobotFileParser`.
   - Compliance: Before issuing any request, `rp.can_fetch()` evaluates whether 
     the target path is permitted. The scraper enforces ethical crawling standards 
     by running single-threaded and maintaining a mandatory 1.0-second delay 
     (`time.sleep(1)`) between successive requests to prevent server congestion.

2. Query Partitioning & Deduplication:
   - Partitioning: Cycles sequentially through chronological terms ("2012" through 
     "2026") followed by single-character alphabetical terms ("a" through "z"). Each 
     unique query forces the backend to generate a fresh pagination pool, bypassing 
     GradCafe's ~340-record pagination depth cap.
   - Deduplication: Uses a Python `Set[str]` (`seen_ids`) for O(1) duplicate lookup, 
     keying off the direct entry URL or a fallback composite signature.

3. HTML Parsing & Atomicity:
   - Target pages are parsed using `bs4.BeautifulSoup` (`html.parser`). Results 
     `<tbody>` rows are iterated, extracting primary columns and traversing nested 
     sub-rows using regex pattern matching (`re.search`) for badges and comment text.
   - Output and state are written atomically to temporary files (`.tmp`) and swapped 
     via `os.replace()` every 5 pages and upon interruption (`KeyboardInterrupt`), 
     ensuring zero file corruption.

4. Data Standardization via Local GPU-Accelerated LLM:
   - A secondary programmatic wrapper (`clean.py`) iterates through the raw output 
     file and passes inputs to the local TinyLlama model via `app.py`.
   - Leverages `llama-cpp-python` compiled with CUDA binary wheels on Python 3.12, 
     fully offloading the model into the NVIDIA RTX 5070's 32GB VRAM to process 
     30,000 records in seconds.
   - Appends standardized fields (`llm-generated-program` and `llm-generated-university`) 
     to each record without destroying original raw data.


SYSTEMATIC CLEANING EDGE CASES & IMPERFECTIONS
--------------------------------------------------------------------------------
1. Edge Cases Handled:
   - Missing / Optional Fields: GPA, individual GRE scores, and status dates are 
     systematically checked against badge text prefixes and assigned explicit `null` values.
   - Date String Parsing: Applicant status strings are isolated using targeted 
     string splitting and regex matching.
   - Multi-line / Noisy Comments: Whitespace, newlines, and HTML tag residue inside user 
     comments are cleaned using `.get_text(strip=True)`.
   - User-Submitted Typos (LLM Standardization): Standardizes inconsistent names 
     into analytics-ready columns.

2. Remaining Imperfections:
   - LLM Hallucinations/Variances: Strict JSON prompting minimizes errors, but 
     ambiguous shorthand inputs may occasionally result in minor standardizations.
   - Raw Comment Fidelity: Natural user-submitted typos within comment text are 
     intentionally preserved to maintain raw data fidelity.


SETUP AND REPRODUCTION INSTRUCTIONS
--------------------------------------------------------------------------------
1. Prerequisites:
   - Ensure Python 3.12 is installed alongside an NVIDIA GPU with CUDA drivers.

2. Installation & Environment Setup:
   - Set up and activate the virtual environment:
     python -3.12 -m venv venv
     venv\Scripts\Activate
   - Install dependencies in both component directories:
     * For the LLM hosting folder:
       cd llm_hosting
       pip install -r requirements.txt
       cd ..
     * For the scraping and cleaning root folder:
       pip install -r requirements.txt
       pip install llama-cpp-python --only-binary=:all: --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

3. Running the Scraper:
   - Execute the main scraping script from the project root directory:
     python scraper.py
   - Generates/updates:
     * `applicant_data.json`: Fully harvested raw dataset.
     * `scraper_state.json`: Checkpoint state file for resumability.

4. Running the Data Cleaning Pipeline:
   - Execute the cleaning wrapper to process data via the local GPU model:
     python clean.py
   - Output: Generates `llm_extend_applicant_data.json` containing appended standardized fields.


KNOWN BUGS
--------------------------------------------------------------------------------
There are no known bugs in this implementation. The script executes without unhandled 
runtime exceptions, handles missing data fields cleanly by assigning `null` values, 
successfully persists data atomically across interruptions, and processes standardizations 
via the local GPU-backed LLM without dropping records.
================================================================================