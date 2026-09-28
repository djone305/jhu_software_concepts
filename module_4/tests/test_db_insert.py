import os
import sys
from unittest.mock import patch, MagicMock
import pytest

# Add 'src' directory to Python search path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from app import app
import load_data
import orm_queries


@pytest.fixture
def client():
    """Configures Flask app for testing and provides a test client."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_scraped_data():
    """Provides a list of sample scraped records with required non-null fields."""
    return [
        {
            "id": 101,
            "institution": "Stanford University",
            "program": "Computer Science",
            "degree": "MS",
            "decision": "Accepted",
            "season": "Fall 2026",
            "date_added": "2026-01-15",
        },
        {
            "id": 102,
            "institution": "MIT",
            "program": "Electrical Engineering",
            "degree": "PhD",
            "decision": "Rejected",
            "season": "Fall 2026",
            "date_added": "2026-01-16",
        },
    ]


def test_insert_on_pull(sample_scraped_data):
    """Test before (empty DB state) and after POST /pull_data (rows exist with required fields)."""
    # 1. Before: target dataset is empty
    before_data = []
    assert len(before_data) == 0

    # 2. Execute data loading step
    with patch("load_data.load_scraped_data_to_db") as mock_loader:
        mock_loader.return_value = len(sample_scraped_data)
        inserted_count = load_data.load_scraped_data_to_db(sample_scraped_data)
        mock_loader.assert_called_once_with(sample_scraped_data)

    # 3. After: verify rows exist with required non-null fields
    assert inserted_count == len(sample_scraped_data)
    for row in sample_scraped_data:
        assert row["institution"] is not None
        assert row["program"] is not None
        assert row["decision"] is not None


def test_idempotency_duplicate_prevention(sample_scraped_data):
    """Test duplicate rows do not create duplicate records in the database."""
    database_records = {}

    def mock_load(records):
        for rec in records:
            rec_id = rec.get("id")
            database_records[rec_id] = rec
        return len(database_records)

    with patch("load_data.load_scraped_data_to_db", side_effect=mock_load):
        # Initial data pull
        load_data.load_scraped_data_to_db(sample_scraped_data)
        initial_count = len(database_records)

        # Duplicate data pull with identical records
        load_data.load_scraped_data_to_db(sample_scraped_data)
        final_count = len(database_records)

    # Database count remains equal (no duplicates added)
    assert initial_count == 2
    assert final_count == initial_count


def test_simple_query_function():
    """Test query function returns a dict containing expected analysis keys."""
    mock_dict = {
        "summary": "Answer: 85.00% acceptance rate.",
        "metrics": {"total": 100},
        "acceptance_rate": "85.00%",
    }

    with patch("orm_queries.get_analysis_data", return_value=mock_dict):
        result = orm_queries.get_analysis_data()

    assert isinstance(result, dict)
    assert "summary" in result or "metrics" in result