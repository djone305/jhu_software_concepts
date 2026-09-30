import sys
from pathlib import Path
import pytest
import requests
from unittest.mock import patch, MagicMock

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from clean import clean_scraped_records, worker_task

@pytest.mark.clean
def test_clean_empty_records():
    assert clean_scraped_records([]) == []

@pytest.mark.clean
@patch("requests.Session.post")
def test_worker_task_200(mock_post):
    """Tests the worker task on a successful 200 response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"cleaned": "data"}
    mock_post.return_value = mock_resp
    
    session = requests.Session()
    success, record, err = worker_task(session, {"id": 1})
    assert success is True
    assert record == {"cleaned": "data"}

@pytest.mark.clean
@patch("requests.Session.post")
def test_worker_task_non_200(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_post.return_value = mock_resp
    
    session = requests.Session()
    success, record, err = worker_task(session, {"id": 1})
    assert success is False

@pytest.mark.clean
@patch("requests.Session.post")
def test_worker_task_exception(mock_post):
    mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
    session = requests.Session()
    success, record, err = worker_task(session, {"id": 1})
    assert success is False