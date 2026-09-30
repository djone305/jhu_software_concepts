import sys
import runpy
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import requests

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from scrape import scrape

@pytest.mark.web
@patch("flask.Flask.run")
def test_app_main_native_execution(mock_run):
    """Natively executes app.py as __main__ to cover line 120 without pragmas."""
    try:
        runpy.run_module("app", run_name="__main__")
    except SystemExit:
        pass
    assert mock_run.called

@pytest.mark.scrape
@patch("scrape.SEARCH_TERMS", ["A"])
@patch("scrape.save_data")
@patch("scrape.get_http_session")
def test_scrape_defensive_branches_native(mock_get_session, mock_save):
    """
    Natively covers scrape.py defensive checks without pragmas:
      - Line 237: len(cols) < 5 (malformed row skipped)
      - Line 304: records_added_this_page == 0 (empty page partition breaker)
    """
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session

    malformed_row_html = b'<html><tbody class="tw-divide-y"><tr><td>Col1</td></tr></tbody></html>'
    empty_tbody_html = b'<html><tbody class="tw-divide-y"></tbody></html>'

    mock_session.get.side_effect = [
        MagicMock(status_code=200, content=malformed_row_html),
        MagicMock(status_code=200, content=empty_tbody_html)
    ]

    scrape(target_count=1, start_term_idx=0, start_page=1)

@pytest.mark.scrape
@patch("scrape.load_existing_data", return_value=([], set(), 0, 1))
@patch("scrape.scrape", return_value=([], set(), 0, 1))
@patch("scrape.save_data")
@patch("sys.argv", ["scrape.py", "--limit", "1"])
def test_scrape_cli_main_native_execution(mock_save, mock_scrape, mock_load):
    """Natively executes scrape.py under __main__ with CLI args to cover line 359 without pragmas."""
    try:
        runpy.run_module("scrape", run_name="__main__")
    except SystemExit:
        pass
    assert mock_scrape.called