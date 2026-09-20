import psycopg

# Connection parameters
conn_params = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Python2026$",
    "host": "localhost",
    "port": "5432"
}

try:
    # Establish connection
    with psycopg.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            # Run a sample query
            cur.execute("SELECT version();")
            db_version = cur.fetchone()
            print("Connected successfully!")
            print(f"PostgreSQL version: {db_version[0]}")
except Exception as e:
    print(f"Error connecting to database: {e}")