from flask import Flask, render_template
from sqlalchemy import func
from models import SessionLocal, Applicant

app = Flask(__name__)

@app.route('/')
def analysis():
    session = SessionLocal()
    try:
        # Question 1: Fall 2026 applicant count
        q1 = session.query(Applicant).filter(Applicant.term.ilike('%Fall 2026%')).count()

        # Question 4: Average GPA of American applicants (Fall 2026)
        q4_avg = session.query(func.avg(Applicant.gpa)).filter(
            Applicant.term.ilike('%Fall 2026%'),
            Applicant.us_or_international.ilike('%American%')
        ).scalar()
        q4 = round(q4_avg, 2) if q4_avg else "N/A"

        # Question 5: Fall 2025 acceptance percentage
        total_2025 = session.query(Applicant).filter(Applicant.term.ilike('%Fall 2025%')).count()
        accepted_2025 = session.query(Applicant).filter(
            Applicant.term.ilike('%Fall 2025%'),
            Applicant.status.ilike('%Accepted%')
        ).count()
        q5 = f"{round((accepted_2025 / total_2025) * 100, 2)}%" if total_2025 > 0 else "N/A"

        # Question 8: Fall 2026 PhD CS acceptances (Original Fields)
        q8 = session.query(Applicant).filter(
            Applicant.term.ilike('%Fall 2026%'),
            Applicant.degree.ilike('%PhD%'),
            Applicant.status.ilike('%Accepted%'),
            Applicant.program.ilike('%Computer Science%')
        ).count()

        # Question 9: Fall 2026 PhD CS acceptances (LLM Fields)
        q9 = session.query(Applicant).filter(
            Applicant.term.ilike('%Fall 2026%'),
            Applicant.degree.ilike('%PhD%'),
            Applicant.status.ilike('%Accepted%'),
            Applicant.llm_generated_program.ilike('%Computer Science%')
        ).count()

        # Custom Question 1: Average GPA of Fall 2026 PhD applicants grouped by status
        cq1_results = session.query(
            Applicant.status, 
            func.avg(Applicant.gpa),
            func.count(Applicant.p_id)
        ).filter(
            Applicant.term.ilike('%Fall 2026%'),
            Applicant.degree.ilike('%PhD%')
        ).group_by(Applicant.status).all()
        
        cq1 = [{"status": r[0], "gpa": round(r[1], 2) if r[1] else "N/A", "count": r[2]} for r in cq1_results if r[0]]

        # Custom Question 2: Count of US vs International Applicants for Fall 2026
        cq2_results = session.query(
            Applicant.us_or_international,
            func.count(Applicant.p_id)
        ).filter(
            Applicant.term.ilike('%Fall 2026%')
        ).group_by(Applicant.us_or_international).all()
        
        cq2 = [{"type": r[0], "count": r[1]} for r in cq2_results if r[0]]

    finally:
        session.close()

    # Pass all results to the HTML template
    return render_template('index.html', q1=q1, q4=q4, q5=q5, q8=q8, q9=q9, cq1=cq1, cq2=cq2)

if __name__ == '__main__':
    app.run(debug=True)