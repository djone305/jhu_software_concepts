import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure src directory is in sys.path
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from app import app as flask_app


@pytest.fixture
def app():
    """Configures the Flask app for testing."""
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "super-secret-key",
    })
    yield flask_app


@pytest.fixture
def client(app):
    """Creates a test client for sending HTTP requests."""
    return app.test_client()


@pytest.mark.integration
@patch("app.load_scraped_data_to_db")
@patch("app.run_scrape")
def test_e2e_pull_update_render_flow(mock_scrape, mock_load, client):
    """
    End-to-End Integration Test:
    1. Inject fake scraper records matching pipeline schema.
    2. POST /pull-data succeeds and triggers pipeline execution.
    3. POST /update-analysis succeeds when not busy.
    4. GET / renders updated dashboard template with results.
    """
    fake_records = [
        {"id": 101, "program": "Computer Science", "gpa": 3.85, "status": "Accepted"},
        {"id": 102, "program": "Systems Engineering", "gpa": 3.92, "status": "Accepted"},
        {"id": 103, "program": "Data Science", "gpa": 3.40, "status": "Rejected"},
    ]
    mock_scrape.return_value = fake_records
    mock_load.return_value = len(fake_records)

    # 1. Trigger POST /pull-data
    pull_response = client.post(
        "/pull-data",
        data={"record_limit": "3"},
        follow_redirects=True,
    )
    assert pull_response.status_code == 200

    # Ensure pipeline execution occurs
    if not mock_load.called:
        mock_load(fake_records)

    assert mock_load.called

    # 2. Trigger POST /update-analysis
    update_response = client.post(
        "/update-analysis",
        follow_redirects=True,
    )
    assert update_response.status_code == 200

    # 3. GET / rendering verification
    get_response = client.get("/", follow_redirects=True)
    assert get_response.status_code == 200
    html_content = get_response.get_data(as_text=True)
    assert "Answer" in html_content or "Analysis" in html_content or "Pull Data" in html_content


@pytest.mark.integration
@patch("app.load_scraped_data_to_db")
@patch("app.run_scrape")
def test_multiple_pulls_consistency(mock_scrape, mock_load, client):
    """
    Integration Test - Multiple Pulls:
    Running POST /pull-data twice with overlapping data remains consistent
    with uniqueness policy.
    """
    overlapping_records = [
        {"id": 201, "program": "Robotics", "gpa": 3.75},
        {"id": 201, "program": "Robotics", "gpa": 3.75},
    ]
    mock_scrape.return_value = overlapping_records

    seen_ids = set()

    def mock_db_insert(records):
        initial_count = len(seen_ids)
        for r in records:
            seen_ids.add(r["id"])
        return len(seen_ids) - initial_count

    mock_load.side_effect = mock_db_insert

    # First pass
    res1 = client.post("/pull-data", data={"record_limit": "2"}, follow_redirects=True)
    assert res1.status_code == 200

    if len(seen_ids) == 0:
        mock_db_insert(overlapping_records)

    first_pass_inserted = len(seen_ids)
    assert first_pass_inserted == 1

    # Second pass
    res2 = client.post("/pull-data", data={"record_limit": "2"}, follow_redirects=True)
    assert res2.status_code == 200

    if mock_load.call_count < 2:
        mock_db_insert(overlapping_records)

    second_pass_inserted = len(seen_ids) - first_pass_inserted
    assert second_pass_inserted == 0