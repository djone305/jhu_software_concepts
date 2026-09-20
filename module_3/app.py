from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from models import SessionLocal, Applicant
import subprocess
import threading
import sys

app = Flask(__name__)
# A secret key is required by Flask to show "flash" messages (success/warning popups)
app.secret_key = 'super_secret_grad_key' 

# Global variables to ensure only ONE scraping process runs at a time
SCRAPING_IN_PROGRESS = False
scraping_lock = threading.Lock()

def run_pipeline():
    """Background task to run the scripts sequentially."""
    global SCRAPING_IN_PROGRESS
    try:
        # sys.executable ensures we use the virtual environment's Python
        python_exe = sys.executable
        
        print("Starting data pull pipeline...")
        # Execute scripts sequentially as requested
        subprocess.run([python_exe, "scrape.py"], check=True)
        subprocess.run([python_exe, "clean.py"], check=True)
        subprocess.run([python_exe, "load_data.py"], check=True)
        subprocess.run([python_exe, "models.py"], check=True)
        subprocess.run([python_exe, "orm_queries.py"], check=True)
        print("Data pull pipeline complete!")
        
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed at script execution: {e}")
    finally:
        # Once finished (or if it fails), release the lock
        with scraping_lock:
            SCRAPING_IN_PROGRESS = False

@app.route('/pull_data', methods=['POST'])
def pull_data():
    global SCRAPING_IN_PROGRESS
    
    with scraping_lock:
        if SCRAPING_IN_PROGRESS:
            # If already running, warn the user and don't start a new process
            flash("A data pull is already in progress. Please wait for it to finish.", "warning")
            return redirect(url_for('analysis'))
        
        # Lock the process
        SCRAPING_IN_PROGRESS = True
        
    # Start the pipeline in a background thread so the webpage doesn't freeze
    thread = threading.Thread(target=run_pipeline)
    thread.start()
    
    # Notify the user it started
    flash("Pull Data initiated! Checking Grad Café for new records. This may take some time (refresh the page later to see updates).", "info")
    return redirect(url_for('analysis'))

@app.route('/')
def analysis():
    session = SessionLocal()
    try:
        # Question 1
        q1 = session.query(Applicant).filter(Applicant.term.ilike('%Fall 2026%')).count()

        # Question 4
        q4_avg = session.query(func.avg(Applicant.gpa)).filter(
            Applicant.term.ilike('%Fall 2026%'),
            Applicant.us_or_international.ilike('%American%')
        ).scalar()
        q4 = round(q4_avg, 2) if q4_avg else "N/A"

        # Question 5
        total_2025 = session.query(Applicant).filter(Applicant.term.ilike('%Fall 2025%')).count()
        accepted_2025 = session.query(Applicant).filter(
            Applicant.term.ilike('%Fall 2025%'),
            Applicant.status.ilike('%Accepted%')
        ).count()
        q5 = f"{round((accepted_2025 / total_2025) * 100, 2)}%" if total_2025 > 0 else "N/A"

        # Question 8
        q8 = session.query(Applicant).filter(
            Applicant.term.ilike('%Fall 2026%'),
            Applicant.degree.ilike('%PhD%'),
            Applicant.status.ilike('%Accepted%'),
            Applicant.program.ilike('%Computer Science%')
        ).count()

        # Question 9
        q9 = session.query(Applicant).filter(
            Applicant.term.ilike('%Fall 2026%'),
            Applicant.degree.ilike('%PhD%'),
            Applicant.status.ilike('%Accepted%'),
            Applicant.llm_generated_program.ilike('%Computer Science%')
        ).count()

        # Custom Question 1
        cq1_results = session.query(
            Applicant.status, 
            func.avg(Applicant.gpa),
            func.count(Applicant.p_id)
        ).filter(
            Applicant.term.ilike('%Fall 2026%'),
            Applicant.degree.ilike('%PhD%')
        ).group_by(Applicant.status).all()
        cq1 = [{"status": r[0], "gpa": round(r[1], 2) if r[1] else "N/A", "count": r[2]} for r in cq1_results if r[0]]

        # Custom Question 2
        cq2_results = session.query(
            Applicant.us_or_international,
            func.count(Applicant.p_id)
        ).filter(
            Applicant.term.ilike('%Fall 2026%')
        ).group_by(Applicant.us_or_international).all()
        cq2 = [{"type": r[0], "count": r[1]} for r in cq2_results if r[0]]

    finally:
        session.close()

    return render_template('index.html', q1=q1, q4=q4, q5=q5, q8=q8, q9=q9, cq1=cq1, cq2=cq2)

if __name__ == '__main__':
    app.run(debug=True)