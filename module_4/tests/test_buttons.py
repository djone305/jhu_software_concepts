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


@pytest.mark.buttons
@patch("app.threading.Thread")
def test_post_pull_data(mock_thread, client):
    """
    Test POST /pull-data:
    1. Returns 200 (following redirect back to index).
    2. Triggers background thread for ETL pipeline execution (mocked).
    """
    # Simulate thread starting behavior
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    response = client.post(
        "/pull-data",
        data={"record_limit": "15"},
        follow_redirects=True,
    )

    # Assert route handles post and redirects to index successfully (Status 200)
    assert response.status_code == 200

    # Assert background thread was initialized and started
    mock_thread.assert_called_once()
    mock_thread_instance.start.assert_called_once()


@pytest.mark.buttons
def test_post_update_analysis_not_busy(client):
    """
    Test POST /update-analysis:
    Returns 200 when not busy (following redirect to index).
    """
    response = client.post(
        "/update-analysis",
        follow_redirects=True,
    )

    # Assert route processes update and redirects back to main dashboard (Status 200)
    assert response.status_code == 200

    html_content = response.get_data(as_text=True)
    # Confirm flash message rendered on the page after update
    assert "Database analysis metrics refreshed." in html_content