Name: Donnell Jones djone305
Course: Modern Concepts in Python
Semester: Fall '26
Module 3 Assignment: Full-Stack Flask & PostgreSQL Dashboard

Skills: Python, Flask, SQLAlchemy, PostgreSQL, BeautifulSoup, ReportLab, HTML/CSS


================================================================================
GRADUATE ADMISSIONS FULL-STACK DASHBOARD & ORM ANALYSIS PIPELINE
================================================================================

PROJECT OVERVIEW
--------------------------------------------------------------------------------
A full-stack Python application that scrapes graduate admissions data from 
Grad Café, loads and cleans records in PostgreSQL, executes ORM analytical 
queries via SQLAlchemy, and serves dynamic results on a Flask web dashboard.


TECHNICAL STACK
--------------------------------------------------------------------------------
- Web Framework: Flask, Jinja2, HTML/CSS
- Database & ORM: PostgreSQL, SQLAlchemy, psycopg2-binary
- Web Scraping: Requests, BeautifulSoup4, Threading
- PDF Reporting: ReportLab


DIRECTORY STRUCTURE
--------------------------------------------------------------------------------
module_3/
│
├── app.py                      # Flask web application & route handlers
├── load_data.py                # Database setup, table schema, & data loaders
├── orm_queries.py              # SQLAlchemy ORM models & analytical queries
├── scrape.py                   # Grad Café web scraper script
├── limitations.py              # Script to generate limitations.pdf
├── requirements.txt           # Project Python dependencies
├── README.txt                 # Project documentation (this file)
├── llm_extend_applicant_data_clean.json # Initial cleaned applicant dataset
│
├── templates/
│   └── index.html              # Dashboard HTML layout
│
└── static/
    └── style.css               # Dashboard styling and alert banners


SETUP AND RUN INSTRUCTIONS
--------------------------------------------------------------------------------
1. Install Dependencies:
   pip install flask sqlalchemy psycopg2-binary beautifulsoup4 requests reportlab

2. Set Environment Variables (PowerShell):
   $env:DB_HOST="localhost"
   $env:DB_PORT="5432"
   $env:DB_NAME="grad_admissions"
   $env:DB_USER="postgres"
   $env:DB_PASSWORD="your_postgres_password"

3. Initialize Database & Load Data:
   python load_data.py

4. Start Flask App:
   python app.py
   Open browser at: http://localhost:5000

5. Generate Limitations PDF:
   python limitations.py


KEY FEATURES
--------------------------------------------------------------------------------
- Live Dashboard Analytics: Renders ORM metrics for Q1, Q4, Q5, Q8, Q9, and custom queries.
- Background Scraping: Pulls 1–100 new records via threaded background workers.
- Concurrency Control: Blocks duplicate scraping jobs while background threads run.
- Update Analysis Button: Instantly refreshes database metrics without triggering a scrape.
- Idempotent Data Ingestion: Auto-provisions PostgreSQL tables and performs UPSERT operations.


KNOWN BUGS
--------------------------------------------------------------------------------
None.
================================================================================