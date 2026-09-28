import os
import sys
from unittest.mock import patch, MagicMock
import pytest

# Add 'src' directory to Python search path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

import app as app_module
from app import app


@pytest.fixture
def client():
    """Configures Flask app for testing and provides a test client."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_busy_state():
    """Ensures scraping_in_progress state is reset before and after each test."""
    app_module.scraping_in_progress = False
    yield
    app_module.scraping_in_progress = False


@patch("app.get_analysis_data")
@patch("app.load_scraped_data_to_db")
@patch("app.run_scrape")
def test_post_pull_data_triggers_loader(
    mock_run_scrape, mock_load_scraped_data_to_db, mock_get_analysis_data, client
):
    """Test POST /pull_data triggers the scraper and passes scraped data to the database loader."""
    mock_get_analysis_data.return_value = {"summary": "Answer: 85% acceptance rate"}
    mock_scraped_records = [{"id": 1, "institution": "Grad School"}]
    mock_run_scrape.return_value = mock_scraped_records

    # Execute background worker synchronously for test assertion
    def execute_sync(target, args=(), daemon=None):
        target(*args)
        return MagicMock()

    with patch("threading.Thread", side_effect=execute_sync):
        response = client.post(
            "/pull_data", data={"record_limit": "5"}, follow_redirects=True
        )

    assert response.status_code == 200
    mock_run_scrape.assert_called_once_with(record_limit=5)
    mock_load_scraped_data_to_db.assert_called_once_with(mock_scraped_records)


@patch("app.get_analysis_data")
def test_post_update_analysis_success(mock_get_analysis_data, client):
    """Test POST /update_analysis returns 200 when not busy."""
    mock_get_analysis_data.return_value = {"summary": "Answer: 85% acceptance rate"}

    response = client.post("/update_analysis", follow_redirects=True)

    assert response.status_code == 200


def test_busy_gating_update_analysis(client):
    """Test POST /update_analysis returns 409 when a pull is in progress."""
    app_module.scraping_in_progress = True

    response = client.post("/update_analysis")

    assert response.status_code == 409


def test_busy_gating_pull_data(client):
    """Test POST /pull_data returns 409 when a pull is in progress."""
    app_module.scraping_in_progress = True

    response = client.post("/pull_data")

    assert response.status_code == 409