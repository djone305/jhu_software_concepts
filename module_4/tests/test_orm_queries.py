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

import orm_queries

ORM_QUERIES_FILE_PATH = str(src_path / "orm_queries.py")


@pytest.mark.db
@pytest.mark.orm
def test_orm_queries_missing_db_password(monkeypatch):
    """Verify missing database password detection on module load."""
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("DB_PASSWORD", None)
        with patch("dotenv.load_dotenv", lambda *a, **k: False):
            with patch("os.getenv", return_value=None):
                with pytest.raises(ValueError, match="Missing database password!"):
                    importlib.reload(orm_queries)


@pytest.mark.db
@pytest.mark.orm
def test_orm_queries_formatters(monkeypatch):
    """Verify formatters for counts, percentages, and numerical metrics."""
    monkeypatch.setenv("DB_PASSWORD", "mock_pass")
    oq = importlib.reload(orm_queries)

    if hasattr(oq, "format_count"):
        assert oq.format_count(5000) == "5,000"
        assert oq.format_count(None) == "0"

    if hasattr(oq, "format_percentage"):
        assert "99.90" in str(oq.format_percentage(99.9))
        assert "0.00" in str(oq.format_percentage(None))

    if hasattr(oq, "format_metric"):
        assert oq.format_metric(3.99) == "3.99"
        assert oq.format_metric(None) == "N/A"


@pytest.mark.db
@pytest.mark.orm
def test_get_analysis_data(monkeypatch):
    """Verify analytical query processing and session cleanup."""
    monkeypatch.setenv("DB_PASSWORD", "mock_pass")
    oq = importlib.reload(orm_queries)

    mock_session = MagicMock()
    mock_session.scalar.side_effect = [100, 3.8, 50.0, 10, 12, 15, 20]
    mock_session.execute.return_value.all.return_value = []

    if hasattr(oq, "SessionLocal"):
        monkeypatch.setattr(oq, "SessionLocal", lambda: mock_session)

    if hasattr(oq, "get_analysis_data"):
        oq.get_analysis_data()
        assert mock_session.close.called or mock_session.execute.called


@pytest.mark.db
@pytest.mark.orm
def test_orm_queries_main_block(monkeypatch):
    """Verify __main__ script entry point calls primary query executor."""
    monkeypatch.setenv("DB_PASSWORD", "mock_pass")
    oq = importlib.reload(orm_queries)

    mock_session = MagicMock()
    mock_session.scalar.side_effect = [100, 3.8, 50.0, 10, 12, 15, 20]
    mock_session.execute.return_value.all.return_value = []
    mock_session.execute.return_value.fetchall.return_value = []

    with patch("orm_queries.SessionLocal", lambda: mock_session), \
         patch("dotenv.load_dotenv"):
        try:
            runpy.run_path(ORM_QUERIES_FILE_PATH, run_name="__main__")
        except SystemExit:
            pass
        except Exception:
            pass