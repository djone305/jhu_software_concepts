import threading
from flask import Flask, render_template, request, redirect, url_for, flash
from orm_queries import get_analysis_data
from scrape import run_scrape
from load_data import load_scraped_data_to_db

app = Flask(__name__)
app.secret_key = "super_secret_grad_cafe_key"

# Global lock and state to track scraping status
scrape_lock = threading.Lock()
scraping_in_progress = False


def background_data_pull(record_limit: int):
    """Background worker function to scrape, clean, and load new records into PostgreSQL."""
    global scraping_in_progress
    try:
        print(f"[BACKGROUND THREAD] Starting pull for {record_limit} records...")
        # Step 1: Scrape N new records from Grad Cafe
        new_records = run_scrape(record_limit=record_limit)
        
        # Step 2: Clean & load newly scraped records into PostgreSQL
        if new_records:
            load_scraped_data_to_db(new_records)
            print(f"[BACKGROUND THREAD] Successfully processed and inserted {len(new_records)} records.")
        else:
            print("[BACKGROUND THREAD] No new records returned from scrape.")
    except Exception as e:
        print(f"[BACKGROUND THREAD ERROR] Scraping process failed: {e}")
    finally:
        with scrape_lock:
            scraping_in_progress = False


@app.route("/")
def index():
    """Renders the dashboard with live database analysis metrics."""
    analysis_data = get_analysis_data()
    return render_template(
        "index.html",
        data=analysis_data,
        scraping_in_progress=scraping_in_progress,
    )


@app.route("/pull_data", methods=["POST"])
def pull_data():
    """Triggered by the frontend form to launch background scraping."""
    global scraping_in_progress

    with scrape_lock:
        if scraping_in_progress:
            flash(
                "A data update is currently in progress. Please wait for it to finish before initiating another Pull Data request.",
                "warning",
            )
            return redirect(url_for("index")), 409
        
        scraping_in_progress = True

    # Parse and sanitize user input limit (capped between 1 and 100)
    try:
        limit_input = int(request.form.get("record_limit", 10))
        record_limit = max(1, min(100, limit_input))
    except (ValueError, TypeError):
        record_limit = 10

    # Dispatch background worker thread so the web UI stays responsive
    thread = threading.Thread(
        target=background_data_pull,
        args=(record_limit,),
        daemon=True
    )
    thread.start()

    flash(
        f"Data pull initialized for up to {record_limit} new records! Click 'Update Analysis' periodically to view updated results.",
        "success"
    )
    return redirect(url_for("index"))


@app.route("/update_analysis", methods=["GET", "POST"])
def update_analysis():
    """Re-queries the PostgreSQL database and refreshes the analysis view without scraping."""
    if scraping_in_progress:
        flash(
            "New data is currently being retrieved in the background. Displaying the most current data available in PostgreSQL.",
            "info"
        )
        return redirect(url_for("index")), 409
    
    flash(
        "Analysis successfully updated with the latest database records.",
        "success"
    )
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)