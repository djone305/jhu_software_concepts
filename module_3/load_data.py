import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

# Fetch database credentials securely from environment variables
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "grad_admissions")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

if not DB_PASSWORD:
    raise ValueError("Missing database password! Set the DB_PASSWORD environment variable.")

def create_database_if_not_exists():
    """Connects to the default 'postgres' database to create the target database if missing."""
    try:
        # Connect to the default postgres maintenance database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        # PostgreSQL requires autocommit to be True to issue a CREATE DATABASE command
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Execute database creation
        cursor.execute(f"CREATE DATABASE {DB_NAME};")
        print(f"Database '{DB_NAME}' created successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.errors.DuplicateDatabase:
        print(f"Database '{DB_NAME}' already exists. Skipping creation.")
    except Exception as e:
        print(f"An error occurred while setting up the database: {e}")

def create_table_if_not_exists(cursor):
    """Creates the strictly defined 'applicants' table if it doesn't exist."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS applicants (
        p_id INTEGER PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        gpa FLOAT,
        gre FLOAT,
        gre_v FLOAT,
        gre_aw FLOAT,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    """
    cursor.execute(create_table_query)

def load_json_to_db(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Now connect to the specifically created target database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    # Ensure table schema matches requirements
    create_table_if_not_exists(cursor)

    # ON CONFLICT (p_id) DO NOTHING ensures idempotency (no duplicates on re-runs)
    insert_query = """
    INSERT INTO applicants (
        p_id, program, comments, date_added, url, status,
        term, us_or_international, gpa, gre, gre_v, gre_aw,
        degree, llm_generated_program, llm_generated_university
    ) VALUES (
        %(p_id)s, %(program)s, %(comments)s, %(date_added)s, %(url)s, %(status)s,
        %(term)s, %(us_or_international)s, %(gpa)s, %(gre)s, %(gre_v)s, %(gre_aw)s,
        %(degree)s, %(llm_generated_program)s, %(llm_generated_university)s
    )
    ON CONFLICT (p_id) DO NOTHING;
    """

    for record in data:
        # Dynamically map keys to handle missing values (.get defaults to None/NULL)
        db_record = {
            "p_id": record.get("p_id") or record.get("entry_id"),
            "program": record.get("program"),
            "comments": record.get("comments"),
            "date_added": record.get("date_added"),
            "url": record.get("url"),
            "status": record.get("status") or record.get("applicant_status"),
            "term": record.get("term"),
            "us_or_international": record.get("us_or_international") or record.get("applicant_type"),
            "gpa": record.get("gpa"),
            "gre": record.get("gre") or record.get("gre_quant"),
            "gre_v": record.get("gre_v") or record.get("gre_verbal"),
            "gre_aw": record.get("gre_aw"),
            "degree": record.get("degree"),
            "llm_generated_program": record.get("llm_generated_program") or record.get("llm-generated-program"),
            "llm_generated_university": record.get("llm_generated_university") or record.get("llm-generated-university")
        }

        # Clean empty strings into standard NULLs for numeric columns to prevent type errors
        for key in ["gpa", "gre", "gre_v", "gre_aw"]:
            if db_record[key] in ["", "N/A", "null"]:
                db_record[key] = None

        # Only insert if there's a valid ID
        if db_record["p_id"] is not None:
            cursor.execute(insert_query, db_record)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database sync complete. New records inserted, duplicates ignored.")

if __name__ == "__main__":
    # 1. Initialize the database safely
    create_database_if_not_exists()
    
    # 2. Target the module_3 directory automatically
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "llm_extend_applicant_data_clean.json")
    
    # 3. Execute the table build and data insertion
    load_json_to_db(json_path)