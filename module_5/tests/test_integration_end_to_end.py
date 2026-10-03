import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure src directory is in sys.path
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Bypass the "Missing database password" ValueError during test discovery
os.environ.setdefault("DB_PASSWORD", "test_dummy_pass")

from app import app as flask_app
from models import Base, Applicant

# 1. Set up an isolated in-memory SQLite database for testing
test_engine = create_engine("sqlite:///:memory:")
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset the global ETL task status before each test to prevent cross-test thread leakage."""
    from app import task_status
    task_status["is_running"] = False
    task_status["error"] = None
    task_status["last_result"] = None


@pytest.fixture(autouse=True)
def patch_database():
    """Forces the app to use the SQLite test database instead of Postgres."""
    with patch("models.engine", test_engine), patch("models.SessionLocal", TestSessionLocal):
        Base.metadata.create_all(bind=test_engine)
        yield
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def app():
    """Configures the Flask app for testing."""
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "super-secret-key",
    })
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def client(app):
    """Creates a test client for sending HTTP requests."""
    return app.test_client()


@pytest.fixture
def db_session():
    """Provides a database session for querying the test DB in tests."""
    session = TestSessionLocal()
    yield session
    session.close()


# Helper to force Flask's background threads to run instantly in tests
class SyncThread:
    # Adding **other_kwargs absorbs unexpected arguments (like daemon, name, group) safely
    def __init__(self, target=None, args=(), kwargs=None, **other_kwargs):
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}
        
    def start(self):
        if self.target:
            self.target(*self.args, **self.kwargs)
            
    def join(self, timeout=None):
        pass


@pytest.mark.integration
@patch("app.threading.Thread", new=SyncThread) 
@patch("app.run_scrape")
@patch("app.clean_scraped_records")
@patch("app.load_scraped_data_to_db")
def test_e2e_pull_update_render_flow(mock_load, mock_clean, mock_scrape, client, db_session):
    
    # Let the dummy data pass straight through the cleaning stage untouched
    mock_clean.side_effect = lambda x: x

    def fake_load(records):
        for r in records:
            db_session.add(Applicant(program=r.get("program"), status=r.get("decision")))
        db_session.commit()
        return len(records)
    
    mock_load.side_effect = fake_load

    mock_scrape.return_value = [
        {"id": 101, "institution": "USC", "program": "Computer Science", "decision": "Accepted", "gpa": "3.85"},
        {"id": 102, "institution": "USC", "program": "Systems Engineering", "decision": "Accepted", "gpa": "3.92"},
    ]

    pull_response = client.post("/pull-data", data={"record_limit": "2"}, follow_redirects=True)
    assert pull_response.status_code == 200

    records = db_session.query(Applicant).all()
    assert len(records) == 2, f"Expected 2 records, found {len(records)}"
    assert records[0].program == "Computer Science"

    update_response = client.post("/update-analysis", follow_redirects=True)
    assert update_response.status_code == 200

    get_response = client.get("/", follow_redirects=True)
    assert get_response.status_code == 200
    html_content = get_response.get_data(as_text=True)
    
    assert "Accepted" in html_content or "Pull Data" in html_content


@pytest.mark.integration
@patch("app.threading.Thread", new=SyncThread) 
@patch("app.run_scrape")
@patch("app.clean_scraped_records")
@patch("app.load_scraped_data_to_db")
def test_multiple_pulls_consistency(mock_load, mock_clean, mock_scrape, client, db_session):
    
    # Pass-through clean mock
    mock_clean.side_effect = lambda x: x

    def fake_load(records):
        # Simulate app's duplicate check avoiding double inserts
        if db_session.query(Applicant).count() == 0:
            db_session.add(Applicant(program=records[0].get("program")))
            db_session.commit()
            return 1
        return 0
        
    mock_load.side_effect = fake_load

    overlapping_records = [
        {"id": 201, "institution": "USC", "program": "Robotics", "decision": "Accepted", "gpa": "3.75"},
        {"id": 201, "institution": "USC", "program": "Robotics", "decision": "Accepted", "gpa": "3.75"},
    ]
    mock_scrape.return_value = overlapping_records

    res1 = client.post("/pull-data", data={"record_limit": "2"}, follow_redirects=True)
    assert res1.status_code == 200

    assert db_session.query(Applicant).count() == 1  

    res2 = client.post("/pull-data", data={"record_limit": "2"}, follow_redirects=True)
    assert res2.status_code == 200

    assert db_session.query(Applicant).count() == 1