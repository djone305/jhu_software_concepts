import psycopg2
import os

# Fetch database credentials securely from environment variables
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "grad_admissions")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if not DB_PASSWORD:
    raise ValueError("Missing database password! Set the DB_PASSWORD environment variable.")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# --- Formatting Helpers ---
def format_count(val):
    """Formats whole numbers with commas (e.g., 19,290)"""
    return f"{int(val):,}" if val is not None else "0"

def format_percentage(val):
    """Formats percentages to 2 decimal places with a % symbol"""
    return f"{float(val):.2f}%" if val is not None else "0.00%"

def format_metric(val):
    """Formats averages to 2 decimal places"""
    return f"{float(val):.2f}" if val is not None else "N/A"

def run_queries():
    conn = get_connection()
    cursor = conn.cursor()
    
    print("="*50)
    print(" SQL Query Analysis Results")
    print("="*50)

    # ---------------------------------------------------------
    # Question 1: Fall 2026 Applicants Count
    # ---------------------------------------------------------
    print("\n--- Question 1 ---")
    print("Question: How many entries in your database are from applicants who applied for Fall 2026?")
    cursor.execute("SELECT COUNT(*) FROM applicants WHERE term ILIKE '%Fall 2026%';")
    q1_result = cursor.fetchone()[0]
    print(f"Fall 2026 applicant count: {format_count(q1_result)}")

    # ---------------------------------------------------------
    # Question 2: Percentage International
    # ---------------------------------------------------------
    print("\n--- Question 2 ---")
    print("Question: Among entries that provide a nationality classification, what percentage are international students?")
    q2_query = """
        SELECT 
            (SUM(CASE WHEN us_or_international ILIKE 'International' THEN 1 ELSE 0 END) * 100.0) / 
            NULLIF(COUNT(us_or_international), 0)
        FROM applicants 
        WHERE us_or_international IS NOT NULL 
          AND TRIM(us_or_international) != '';
    """
    cursor.execute(q2_query)
    q2_result = cursor.fetchone()[0]
    print(f"Percent international: {format_percentage(q2_result)}")

    # ---------------------------------------------------------
    # Question 3: Average Metrics
    # ---------------------------------------------------------
    print("\n--- Question 3 ---")
    print("Question: What are the average GPA, GRE Quantitative, GRE Verbal, and GRE Analytical Writing scores of applicants who provide each metric?")
    cursor.execute("SELECT AVG(gpa), AVG(gre), AVG(gre_v), AVG(gre_aw) FROM applicants;")
    q3_result = cursor.fetchone()
    print(f"Average GPA: {format_metric(q3_result[0])}")
    print(f"Average GRE Quantitative: {format_metric(q3_result[1])}")
    print(f"Average GRE Verbal: {format_metric(q3_result[2])}")
    print(f"Average GRE Analytical Writing: {format_metric(q3_result[3])}")

    # ---------------------------------------------------------
    # Question 4: Average GPA - American Fall 2026
    # ---------------------------------------------------------
    print("\n--- Question 4 ---")
    print("Question: What is the average GPA of American applicants who applied for Fall 2026?")
    q4_query = """
        SELECT AVG(gpa) FROM applicants 
        WHERE term ILIKE '%Fall 2026%' 
          AND us_or_international ILIKE 'American';
    """
    cursor.execute(q4_query)
    q4_result = cursor.fetchone()[0]
    print(f"Average GPA of American applicants (Fall 2026): {format_metric(q4_result)}")

    # ---------------------------------------------------------
    # Question 5: Percentage Fall 2025 Acceptances
    # ---------------------------------------------------------
    print("\n--- Question 5 ---")
    print("Question: What percentage of Fall 2025 entries are acceptances?")
    q5_query = """
        SELECT 
            (SUM(CASE WHEN status ILIKE '%Accept%' THEN 1 ELSE 0 END) * 100.0) / 
            NULLIF(COUNT(*), 0)
        FROM applicants 
        WHERE term ILIKE '%Fall 2025%';
    """
    cursor.execute(q5_query)
    q5_result = cursor.fetchone()[0]
    print(f"Fall 2025 acceptance percentage: {format_percentage(q5_result)}")

    # ---------------------------------------------------------
    # Question 6: Average GPA - Accepted Fall 2026
    # ---------------------------------------------------------
    print("\n--- Question 6 ---")
    print("Question: What is the average GPA of accepted applicants who applied for Fall 2026?")
    q6_query = """
        SELECT AVG(gpa) FROM applicants 
        WHERE term ILIKE '%Fall 2026%' 
          AND status ILIKE '%Accept%';
    """
    cursor.execute(q6_query)
    q6_result = cursor.fetchone()[0]
    print(f"Average GPA of accepted applicants (Fall 2026): {format_metric(q6_result)}")

    # ---------------------------------------------------------
    # Question 7: Johns Hopkins - Master's in CS (Original Fields)
    # ---------------------------------------------------------
    print("\n--- Question 7 ---")
    print("Question: How many entries are from applicants who applied to Johns Hopkins University for a master's degree in Computer Science?")
    q7_query = """
        SELECT COUNT(*) FROM applicants 
        WHERE (program ILIKE '%Johns Hopkins%' OR program ~* '\\bJHU\\b') 
          AND program ILIKE '%Computer Science%' 
          AND degree ILIKE '%Master%';
    """
    cursor.execute(q7_query)
    q7_result = cursor.fetchone()[0]
    print(f"JHU Master's CS applicant count: {format_count(q7_result)}")

    # ---------------------------------------------------------
    # Question 8: 4 Universities - PhD CS Acceptances Fall 2026 (Original Fields)
    # ---------------------------------------------------------
    print("\n--- Question 8 ---")
    print("Question: How many Fall 2026 entries are acceptances from applicants applying for a PhD in Computer Science at Georgetown, MIT, Stanford, or Carnegie Mellon (using original fields)?")
    q8_query = """
        SELECT COUNT(*) FROM applicants 
        WHERE term ILIKE '%Fall 2026%'
          AND status ILIKE '%Accept%'
          AND (degree ILIKE '%PhD%' OR degree ~* '\\bPh\\.?D\\b')
          AND program ILIKE '%Computer Science%'
          AND (
              program ILIKE '%Georgetown%' OR 
              program ILIKE '%Massachusetts Institute of Technology%' OR program ~* '\\bMIT\\b' OR
              program ILIKE '%Stanford%' OR 
              program ILIKE '%Carnegie Mellon%' OR program ~* '\\bCMU\\b'
          );
    """
    cursor.execute(q8_query)
    q8_result = cursor.fetchone()[0]
    print(f"Original-field count: {format_count(q8_result)}")

    # ---------------------------------------------------------
    # Question 9: 4 Universities - PhD CS Acceptances Fall 2026 (LLM Fields)
    # ---------------------------------------------------------
    print("\n--- Question 9 ---")
    print("Question: Repeat Question 8 using the LLM-generated university and program fields, and compare the results.")
    q9_query = """
        SELECT COUNT(*) FROM applicants 
        WHERE term ILIKE '%Fall 2026%'
          AND status ILIKE '%Accept%'
          AND (degree ILIKE '%PhD%' OR degree ~* '\\bPh\\.?D\\b')
          AND llm_generated_program ILIKE '%Computer Science%'
          AND (
              llm_generated_university ILIKE '%Georgetown%' OR 
              llm_generated_university ILIKE '%Massachusetts Institute of Technology%' OR llm_generated_university ~* '\\bMIT\\b' OR
              llm_generated_university ILIKE '%Stanford%' OR 
              llm_generated_university ILIKE '%Carnegie Mellon%' OR llm_generated_university ~* '\\bCMU\\b'
          );
    """
    cursor.execute(q9_query)
    q9_result = cursor.fetchone()[0]
    
    diff = q9_result - q8_result
    sign = "+" if diff > 0 else ""
    
    print(f"Original-field count: {format_count(q8_result)}")
    print(f"LLM-field count: {format_count(q9_result)}")
    print(f"Difference: {sign}{diff}")

    # ---------------------------------------------------------
    # Custom Question 1: Average GPA by Admission Status (Fall 2026 PhDs)
    # ---------------------------------------------------------
    print("\n--- Custom Question 1 ---")
    print("Question: What is the average GPA of Fall 2026 PhD applicants, grouped by their admission status?")
    
    # FIX: Grouping raw status strings creates fragmented rows. This CASE statement 
    # normalizes statuses into 3 distinct buckets before performing the GROUP BY.
    q10_query = """
        SELECT 
            CASE 
                WHEN status ILIKE '%Accept%' THEN 'Accepted'
                WHEN status ILIKE '%Reject%' THEN 'Rejected'
                WHEN status ILIKE '%Wait%' THEN 'Waitlisted'
                ELSE 'Other'
            END AS normalized_status, 
            AVG(gpa) AS avg_gpa, 
            COUNT(*) AS total_applicants
        FROM applicants
        WHERE term ILIKE '%Fall 2026%'
          AND (degree ILIKE '%PhD%' OR degree ~* '\\bPh\\.?D\\b')
          AND gpa IS NOT NULL
          AND (status ILIKE '%Accept%' OR status ILIKE '%Reject%' OR status ILIKE '%Wait%')
        GROUP BY 1
        ORDER BY avg_gpa DESC;
    """
    cursor.execute(q10_query)
    q10_results = cursor.fetchall()
    
    for row in q10_results:
        status = row[0]
        avg_gpa = format_metric(row[1])
        count = format_count(row[2])
        # FIX: Formatted with :<10 to keep the columns cleanly aligned in the terminal output
        print(f"Status: {status:<10} | Average GPA: {avg_gpa} | Count: {count}")

    # ---------------------------------------------------------
    # Custom Question 2: Top 5 Universities by Application Volume (Fall 2026)
    # ---------------------------------------------------------
    print("\n--- Custom Question 2 ---")
    print("Question: Which 5 universities received the most Fall 2026 applications, and what is their average GRE Quant score?")
    q11_query = """
        SELECT 
            llm_generated_university, 
            COUNT(*) AS application_count, 
            AVG(gre) AS avg_gre_quant
        FROM applicants
        WHERE term ILIKE '%Fall 2026%'
          AND llm_generated_university IS NOT NULL
        GROUP BY llm_generated_university
        ORDER BY application_count DESC
        LIMIT 5;
    """
    cursor.execute(q11_query)
    q11_results = cursor.fetchall()
    
    for i, row in enumerate(q11_results, 1):
        uni = row[0]
        count = format_count(row[1])
        avg_gre = format_metric(row[2])
        print(f"{i}. {uni} | Applications: {count} | Average GRE Quant: {avg_gre}")

    print("\n" + "="*50)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_queries()