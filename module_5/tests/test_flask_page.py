import sys
from pathlib import Path

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
        "SERVER_NAME": "localhost",
    })
    yield flask_app


@pytest.fixture
def client(app):
    """Creates a test client for sending HTTP requests."""
    return app.test_client()


@pytest.mark.web
def test_app_factory_and_routes(app):
    """Assert a testable Flask app exists and required routes/configurations are set."""
    assert app is not None
    assert app.config["TESTING"] is True

    # Retrieve registered endpoints from app url_map
    registered_routes = [rule.rule for rule in app.url_map.iter_rules()]

    # Assert base routes exist
    assert "/" in registered_routes
    assert "/update-analysis" in registered_routes
    assert "/pull-data" in registered_routes
    assert "/pull-status" in registered_routes


@pytest.mark.web
def test_get_analysis_page_load(client):
    """
    Test GET request for the analysis page.
    Validates Status 200, essential buttons, and required text content.
    """
    # Fetch root dashboard
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200

    html_content = response.get_data(as_text=True)

    # Assert required buttons exist in HTML
    assert "Pull Data" in html_content
    assert "Update Analysis" in html_content

    # Assert required page text exists
    assert "Analysis" in html_content
    assert "Answer:" in html_content