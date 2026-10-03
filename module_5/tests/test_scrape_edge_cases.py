import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import requests

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from scrape import scrape

@pytest.mark.scrape
@patch("scrape.SEARCH_TERMS", ["A", "B", "C"])
@patch("scrape.save_data")
@patch("scrape.get_http_session")
def test_scrape_unreachable_lines(mock_get_session, mock_save):
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    
    resp_timeout = requests.exceptions.RequestException("Timeout")
    resp_short_row = MagicMock(status_code=200, content=b"<html><tbody class='tw-divide-y'><tr><td>1</td><td>2</td><td>3</td><td>4</td></tr></tbody></html>")
    resp_no_tbody = MagicMock(status_code=200, content=b"<html><body></body></html>")
    resp_valid = MagicMock(status_code=200, content=b"<html><tbody class='tw-divide-y'><tr><td>USC</td><td><div class='tw-text-gray-900'><span>CS</span></div></td><td>10/10</td><td>Accepted</td><td><a href='/1'>L</a></td></tr></tbody></html>")

    # Intelligent mock that won't run out of items (fixes StopIteration)
    def mock_get(*args, **kwargs):
        url = args[0]
        if "page=1" in url and "q=A" in url:
            raise resp_timeout
        elif "q=A" in url:
            return resp_short_row
        elif "q=B" in url:
            return resp_no_tbody
        elif "q=C" in url and "page=4" in url:
            return resp_valid
        elif "q=C" in url and "page=5" in url:
            return resp_valid
        else:
            return resp_no_tbody

    mock_session.get.side_effect = mock_get
    
    scrape(target_count=10, start_term_idx=0, start_page=1)
    scrape(target_count=10, start_term_idx=2, start_page=4)
    
    assert mock_save.called
