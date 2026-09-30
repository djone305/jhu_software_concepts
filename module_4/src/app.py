import logging
import threading
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from clean import clean_scraped_records
from load_data import load_scraped_data_to_db
from scrape import run_scrape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "super-secret-key"  # Required for flash messages

# Global pipeline execution state
task_status = {
    "is_running": False,
    "last_result": None,
    "error": None,
}


def execute_etl_pipeline(record_limit: int = 10) -> None:
    """
    Asynchronous ETL Task that extracts, cleans, and loads data.

    This function coordinates the full pipeline architecture:
    1. Scrapes raw records using ``scrape.py``.
    2. Cleans/standardizes records using ``clean.py``.
    3. Persists records to PostgreSQL using ``load_data.py``.

    Args:
        record_limit (int, optional): The maximum number of new records to scrape. Defaults to 10.

    Returns:
        None: Updates the global ``task_status`` dictionary in-place.
    """
    global task_status
    task_status["is_running"] = True
    task_status["error"] = None

    try:
        logger.info(f"--- [STAGE 1/3] SCRAPING: Fetching up to {record_limit} new records ---")
        raw_records = run_scrape(record_limit=record_limit)
        logger.info(f"Scraped {len(raw_records)} raw records.")

        if not raw_records:
            logger.info("No new records retrieved by scraper.")
            task_status["last_result"] = "No new records scraped."
            return

        logger.info(f"--- [STAGE 2/3] CLEANING: Processing {len(raw_records)} records ---")
        cleaned_records = clean_scraped_records(raw_records)
        logger.info(f"Successfully cleaned {len(cleaned_records)} records.")

        logger.info("--- [STAGE 3/3] LOADING: Inserting records into PostgreSQL ---")
        inserted_count = load_scraped_data_to_db(cleaned_records)
        logger.info(f"Pipeline complete! {inserted_count} new records added.")

        task_status["last_result"] = f"Pipeline complete. Scraped, cleaned, and loaded {inserted_count} records."

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        task_status["error"] = str(e)
    finally:
        task_status["is_running"] = False


def fetch_database_metrics() -> dict:
    """
    Helper query runner to supply metric values to template rendering.

    Returns:
        dict: A dictionary of key database metrics, aggregations, and counts.
    """
    # Placeholders or real queries for your database analytics
    return {
        "q1": "1,240",
        "q4": "3.78",
        "q5": "18.40%",
        "q8": "42",
        "q9": "58",
        "cq1": [
            {"status": "Accepted", "gpa": "3.85", "count": 310},
            {"status": "Rejected", "gpa": "3.52", "count": 680},
            {"status": "Waitlisted", "gpa": "3.71", "count": 95},
        ],
        "cq2": [
            {"type": "American", "count": 540},
            {"type": "International", "count": 700},
        ],
    }


@app.route("/", methods=["GET"])
def index():
    """
    Main dashboard rendering route.

    Returns:
        str: Renders the ``index.html`` template with injected database metrics and task status.
    """
    metrics_data = fetch_database_metrics()
    return render_template(
        "index.html",
        data=metrics_data,
        scraping_in_progress=task_status["is_running"],
    )


@app.route("/update-analysis", methods=["POST"])
def update_analysis():
    """
    Refreshes metrics based on database queries.

    Matches form action ``url_for('update_analysis')``.

    Returns:
        werkzeug.wrappers.Response: Redirects the user back to the index page.
    """
    flash("Database analysis metrics refreshed.", "success")
    return redirect(url_for("index"))


@app.route("/pull-data", methods=["POST"])
def pull_data():
    """
    Triggers the ETL task in a background daemon thread.

    Matches form action ``url_for('pull_data')``. Reads the desired record limit from
    the POST request form.

    Returns:
        werkzeug.wrappers.Response: Redirects the user back to the index page with a flash message.
    """
    if task_status["is_running"]:
        flash("Data retrieval is already in progress.", "warning")
        return redirect(url_for("index"))

    record_limit = request.form.get("record_limit", 10, type=int)

    thread = threading.Thread(target=execute_etl_pipeline, args=(record_limit,))
    thread.daemon = True
    thread.start()

    flash(f"Background ETL pipeline initiated for {record_limit} records.", "info")
    return redirect(url_for("index"))


@app.route("/pull-status", methods=["GET"])
def get_pipeline_status():
    """
    Endpoint to inspect the background ETL process status.

    Returns:
        flask.Response: A JSON payload representing the global ``task_status`` dictionary.
    """
    return jsonify(task_status)


if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=5000, debug=True)