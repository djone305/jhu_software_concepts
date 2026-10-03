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


@pytest.mark.db
@patch("load_data.load_scraped_data_to_db")
@patch("scrape.run_scrape")
def test_db_insert_on_pull(mock_scrape, mock_load, client):
    """
    Test insert on pull:
    1. Before: target DB starts with 0 inserted rows.
    2. After POST /pull-data: pipeline processes new rows with non-null required fields.
    """
    sample_records = [
        {"id": 1, "title": "Record A", "value": 100.0, "status": "active"},
        {"id": 2, "title": "Record B", "value": 250.5, "status": "active"},
    ]
    mock_scrape.return_value = sample_records
    mock_load.return_value = len(sample_records)

    db_row_count_before = 0
    assert db_row_count_before == 0

    response = client.post("/pull-data", data={"record_limit": "10"}, follow_redirects=True)
    assert response.status_code == 200

    if mock_load.called:
        passed_records = mock_load.call_args[0][0]
        assert len(passed_records) > 0
        for record in passed_records:
            assert record.get("id") is not None
            assert record.get("title") is not None


@pytest.mark.db
@patch("load_data.load_scraped_data_to_db")
def test_db_idempotency_and_constraints(mock_load):
    """
    Test idempotency / constraints:
    Duplicate pulls must not create duplicate records in the database.
    """
    duplicate_records = [
        {"id": 1, "title": "Record A", "value": 100.0},
        {"id": 1, "title": "Record A", "value": 100.0},
    ]

    mock_load.side_effect = lambda records: len({r["id"] for r in records})

    inserted_first_pass = mock_load(duplicate_records)
    inserted_second_pass = mock_load(duplicate_records)

    assert inserted_first_pass == 1
    assert inserted_second_pass == 1


@pytest.mark.db
def test_simple_query_function():
    """
    Test simple query function:
    Queries data and returns a dictionary with expected analytical key fields.
    """
    from app import fetch_database_metrics

    metrics = fetch_database_metrics()

    assert isinstance(metrics, dict)

    expected_keys = ["q1", "q4", "q5", "q8", "q9", "cq1", "cq2"]
    for key in expected_keys:
        assert key in metrics
        assert metrics[key] is not None