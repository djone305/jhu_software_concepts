import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import load_data
from load_data import safe_float

@pytest.mark.load_data
def test_safe_float():
    assert safe_float("3.85") == 3.85
    assert safe_float(None) is None
    assert safe_float("invalid") is None

@pytest.mark.load_data
def test_load_empty_records():
    assert load_data.load_scraped_data_to_db([]) == 0

@pytest.mark.load_data
def test_load_success():
    """Manually intercepts the database connection in memory to guarantee isolation."""
    mock_session_cls = MagicMock()
    mock_session = mock_session_cls.return_value
    
    # Save original references
    orig_session = load_data.SessionLocal
    orig_applicant = load_data.Applicant
    
    try:
        # Forcefully overwrite the variables in the loaded module
        load_data.SessionLocal = mock_session_cls
        load_data.Applicant = MagicMock()
        
        records = [{"University": "USC", "GPA": "4.0"}]
        count = load_data.load_scraped_data_to_db(records)
        
        assert count == 1
        assert mock_session.add.called
        assert mock_session.commit.called
    finally:
        # Restore originals
        load_data.SessionLocal = orig_session
        load_data.Applicant = orig_applicant

@pytest.mark.load_data
def test_load_exception():
    mock_session_cls = MagicMock()
    mock_session = mock_session_cls.return_value
    mock_session.commit.side_effect = Exception("Simulated DB Crash")
    
    orig_session = load_data.SessionLocal
    orig_applicant = load_data.Applicant
    
    try:
        load_data.SessionLocal = mock_session_cls
        load_data.Applicant = MagicMock()
        
        records = [{"University": "Test U"}]
        with pytest.raises(Exception, match="Simulated DB Crash"):
            load_data.load_scraped_data_to_db(records)
            
        assert mock_session.rollback.called
    finally:
        load_data.SessionLocal = orig_session
        load_data.Applicant = orig_applicant