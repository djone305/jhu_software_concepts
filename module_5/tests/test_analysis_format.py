import re
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
        "SECRET_KEY": "super-secret-key",
    })
    yield flask_app


@pytest.fixture
def client(app):
    """Creates a test client for sending HTTP requests."""
    return app.test_client()


@pytest.mark.analysis
def test_analysis_labels_and_percentage_formatting(client):
    """
    Test GET / or /analysis endpoint:
    1. Validates that rendered page includes 'Answer' labels.
    2. Validates that percentage metrics on the page are formatted with exactly two decimals.
    """
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200

    html_content = response.get_data(as_text=True)

    # 1. Assert page includes "Answer" labels
    assert "Answer" in html_content

    # 2. Extract percentage values from rendered page and assert two-decimal formatting (e.g., 18.40%)
    percentage_matches = re.findall(r"\d+\.?\d*%", html_content)
    assert len(percentage_matches) > 0, "No percentage metrics found on rendered page."

    for pct in percentage_matches:
        assert re.match(r"^\d+\.\d{2}%$", pct), f"Percentage '{pct}' is not formatted with two decimal places."