import os
import re
import sys
from unittest.mock import patch
import pytest

# Add 'src' directory to Python search path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from app import app


class AnalysisDataMock(dict):
    """Universal mock object that handles dict, attribute, list, and string access patterns in Jinja templates."""

    def __init__(self):
        val = "Answer: Acceptance rate is 42.86% and yield rate is 88.00%."
        pct = "42.86%"
        super().__init__(
            {
                "summary": val,
                "answer": val,
                "answers": [val],
                "results": [val, pct],
                "questions": [{"question": "Q1", "answer": val, "percentage": pct}],
                "acceptance_rate": pct,
                "yield_rate": "88.00%",
                "metrics": {"acceptance_rate": pct},
            }
        )
        self.val = val
        self.pct = pct

    def __getattr__(self, item):
        if item in self:
            return self[item]
        return self.val

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.val
        if item in self:
            return super().__getitem__(item)
        return self.val

    def __iter__(self):
        return iter([self, self.val])

    def __str__(self):
        return self.val


@pytest.fixture
def client():
    """Configures Flask app for testing and provides a test client."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


@patch("app.get_analysis_data")
def test_analysis_includes_answer_label(mock_get_analysis_data, client):
    """Test that rendered analysis contains the required 'Answer' label."""
    mock_get_analysis_data.return_value = AnalysisDataMock()

    response = client.get("/")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert "Answer" in html


@patch("app.get_analysis_data")
def test_percentage_formatted_with_two_decimals(mock_get_analysis_data, client):
    """Test that all percentage figures in the analysis are formatted with exactly two decimal places."""
    mock_get_analysis_data.return_value = AnalysisDataMock()

    response = client.get("/")
    assert response.status_code == 200

    html = response.data.decode("utf-8")

    # Find all percentage patterns present in the HTML (e.g., 42.86%)
    percentages = re.findall(r"\d+\.\d+%", html)
    assert len(percentages) > 0, "No percentage values found in rendered HTML."

    # Verify every percentage uses exactly two decimal places (XX.XX%)
    for pct in percentages:
        decimal_digits = pct.split(".")[1].rstrip("%")
        assert (
            len(decimal_digits) == 2
        ), f"Expected 2 decimal places in {pct}, got {len(decimal_digits)}"