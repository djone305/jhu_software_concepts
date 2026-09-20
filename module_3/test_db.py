from models import SessionLocal, Applicant

session = SessionLocal()
try:
    # Check total rows
    total_count = session.query(Applicant).count()
    print(f"Total rows in PostgreSQL 'applicants' table: {total_count}\n")
    
    if total_count > 0:
        print("Sample of first 3 rows in the database:")
        sample_rows = session.query(Applicant).limit(3).all()
        for i, row in enumerate(sample_rows):
            print(f"  [{i+1}] term: '{row.term}' | status: '{row.status}' | degree: '{row.degree}' | gpa: {row.gpa}")
    else:
        print("The table is currently empty. This means your data-loading script populated a local file (like SQLite) instead of this PostgreSQL database.")
finally:
    session.close()