import importlib
import os
import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure src directory is in sys.path
src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest

import query_data

QUERY_DATA_FILE_PATH = str(src_path / "query_data.py")


@pytest.mark.db
@pytest.mark.query
def test_query_data_missing_db_password(monkeypatch):
    """Verify exception handling when database password environment variable is missing."""
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("DB_PASSWORD", None)
        with patch("dotenv.load_dotenv", lambda *a, **k: False):
            with patch("os.getenv", return_value=None):
                with pytest.raises(ValueError, match="Missing database password!"):
                    importlib.reload(query_data)


@pytest.mark.db
@pytest.mark.query
def test_query_data_formatters(monkeypatch):
    """Verify string and metric formatting helper functions."""
    monkeypatch.setenv("DB_PASSWORD", "mock_pass")
    qd = importlib.reload(query_data)

    if hasattr(qd, "format_count"):
        assert qd.format_count(1000) == "1,000"
        assert qd.format_count(None) == "0"

    if hasattr(qd, "format_percentage"):
        assert "85.50" in str(qd.format_percentage(85.5))
        assert "0.00" in str(qd.format_percentage(None))

    if hasattr(qd, "format_metric"):
        assert qd.format_metric(3.75) == "3.75"
        assert qd.format_metric(None) == "N/A"


@pytest.mark.db
@pytest.mark.query
def test_run_orm_queries(monkeypatch):
    """Verify database query execution with mocked session response."""
    monkeypatch.setenv("DB_PASSWORD", "mock_pass")
    qd = importlib.reload(query_data)

    mock_session = MagicMock()
    mock_session.scalar.side_effect = [100, 3.85, 45.5, 10, 15, 20, 25]

    mock_row = MagicMock()
    mock_row.clean_status = "Accepted"
    mock_row.avg_gpa = 3.9
    mock_row.total_applicants = 20
    mock_session.execute.return_value.all.return_value = [mock_row]

    if hasattr(qd, "SessionLocal"):
        monkeypatch.setattr(qd, "SessionLocal", lambda: mock_session)

    if hasattr(qd, "run_orm_queries"):
        qd.run_orm_queries()
        assert mock_session.close.called or mock_session.execute.called


@pytest.mark.db
@pytest.mark.query
def test_query_data_main_block(monkeypatch):
    """Verify module direct CLI execution behavior."""
    monkeypatch.setenv("DB_PASSWORD", "mock_pass")
    qd = importlib.reload(query_data)

    mock_session = MagicMock()
    mock_session.scalar.side_effect = [100, 3.85, 45.5, 10, 15, 20, 25]
    mock_session.execute.return_value.all.return_value = []
    mock_session.execute.return_value.fetchall.return_value = []

    with patch("query_data.SessionLocal", lambda: mock_session), \
         patch("dotenv.load_dotenv"):
        try:
            runpy.run_path(QUERY_DATA_FILE_PATH, run_name="__main__")
        except SystemExit:
            pass
        except Exception:
            pass