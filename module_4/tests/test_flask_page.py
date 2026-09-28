import os
import sys
import pytest
from unittest.mock import patch

# Dynamically add the 'src' directory to Python's search path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from app import app


@pytest.fixture
def client():
    """Configures Flask app for testing and provides a test client."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


def test_app_routes_configured():
    """Assert that required routes are defined in the Flask app."""
    registered_routes = [rule.rule for rule in app.url_map.iter_rules()]

    assert "/" in registered_routes
    assert "/pull_data" in registered_routes
    assert "/update_analysis" in registered_routes


@patch("app.get_analysis_data")
def test_get_analysis_page_load(mock_get_analysis_data, client):
    """Test page load status 200 and verify required content/buttons."""
    # Mock database return data so tests pass independently of live DB
    mock_get_analysis_data.return_value = {
        "summary": "Answer: 85% acceptance rate calculated.",
        "metrics": {"total_applicants": 100},
    }

    # Execute GET request
    response = client.get("/")

    # 1. Assert HTTP Status 200
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # 2. Assert page contains required buttons/text
    assert "Pull Data" in html
    assert "Update Analysis" in html

    # 3. Assert page text includes 'Analysis' and at least one 'Answer:'
    assert "Analysis" in html
    assert "Answer:" in html