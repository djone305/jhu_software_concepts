import json
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Fetch database credentials from environment variables with sensible defaults
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "grad_admissions")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")  # Fallback default if env var is unset


def create_database_if_not_exists():
    """Connects to the default 'postgres' database to create the target database if missing."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE DATABASE {DB_NAME};")
        print(f"Database '{DB_NAME}' created successfully!")
        
        cursor.close()
        conn.close()
    except psycopg2.errors.DuplicateDatabase:
        pass
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


def process_and_insert_records(cursor, records):
    """Formats, cleans, and inserts or updates a list of record dictionaries in PostgreSQL."""
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
    ON CONFLICT (p_id) DO UPDATE SET
        program = EXCLUDED.program,
        comments = EXCLUDED.comments,
        status = EXCLUDED.status,
        term = EXCLUDED.term,
        us_or_international = EXCLUDED.us_or_international,
        gpa = EXCLUDED.gpa,
        gre = EXCLUDED.gre,
        gre_v = EXCLUDED.gre_v,
        gre_aw = EXCLUDED.gre_aw,
        degree = EXCLUDED.degree,
        llm_generated_program = EXCLUDED.llm_generated_program,
        llm_generated_university = EXCLUDED.llm_generated_university;
    """

    for record in records:
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

        # Convert empty/invalid strings to Python None (PostgreSQL NULL)
        for key in ["gpa", "gre", "gre_v", "gre_aw"]:
            val = db_record[key]
            if val in ["", "N/A", "null", None]:
                db_record[key] = None
            else:
                try:
                    db_record[key] = float(val)
                except (ValueError, TypeError):
                    db_record[key] = None

        if db_record["p_id"] is not None:
            cursor.execute(insert_query, db_record)


def load_scraped_data_to_db(records):
    """Import function called by app.py to write freshly scraped lists into PostgreSQL."""
    if not records:
        print("[DATABASE] No records provided to insert.")
        return

    create_database_if_not_exists()

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    create_table_if_not_exists(cursor)
    process_and_insert_records(cursor, records)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"[DATABASE] Processed and upserted {len(records)} records into PostgreSQL.")


def load_json_to_db(json_file_path):
    """Loads initial data from a local JSON file into the database."""
    if not os.path.exists(json_file_path):
        print(f"[DATABASE ERROR] JSON file not found at: {json_file_path}")
        return

    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    create_database_if_not_exists()

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    create_table_if_not_exists(cursor)
    process_and_insert_records(cursor, data)

    conn.commit()
    cursor.close()
    conn.close()
    print("[DATABASE] Initial JSON sync complete.")


if __name__ == "__main__":
    create_database_if_not_exists()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "llm_extend_applicant_data_clean.json")
    load_json_to_db(json_path)