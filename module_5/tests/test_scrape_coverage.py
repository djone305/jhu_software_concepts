import sys
from pathlib import Path
import pytest
from unittest.mock import patch, mock_open, MagicMock
import requests

src_path = Path(__file__).resolve().parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from scrape import get_record_id, load_existing_data, scrape

@pytest.mark.scrape
def test_get_record_id_fallback():
    rec_id = get_record_id(None, "USC", "CS", "10/10/2026", "Accepted")
    assert rec_id == "USC|CS|10/10/2026|Accepted"

@pytest.mark.scrape
@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="{invalid_json}")
def test_load_existing_data_json_error(mock_file, mock_exists):
    """Tests the JSONDecodeError edge case."""
    data, seen, term, page = load_existing_data("dummy.json", "dummy_state.json")
    assert data == []
    assert term == 0

@pytest.mark.scrape
@patch("scrape.SEARCH_TERMS", ["A"]) 
@patch("scrape.save_data")
@patch("scrape.get_http_session")
def test_scrape_main_loop_edge_cases(mock_get_session, mock_save):
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    
    # Mega-payload designed to hit every string-parsing if/else branch
    valid_html = b'''
    <html>
    <tbody class="tw-divide-y">
        <tr>
            <td>USC</td>
            <td><div class="tw-text-gray-900"><span>CS</span><span>PhD</span></div></td>
            <td>10/10/2026</td>
            <td>Accepted on 10/11</td>
            <td><a href="/test">Link</a></td>
        </tr>
        <tr>
            <td>
                <div class="tw-rounded-md">Fall 2026</div>
                <div class="tw-rounded-md">GPA 4.0</div>
                <div class="tw-rounded-md">GRE 320</div>
                <div class="tw-rounded-md">GRE V 160</div>
                <div class="tw-rounded-md">GRE AW 5.0</div>
                <div class="tw-rounded-md">American</div>
                <p class="tw-text-gray-500 tw-text-sm">Nice!</p>
            </td>
        </tr>
        <tr>
            <td>MIT</td>
            <td><div class="tw-text-gray-900"><span>Math</span><span>Masters</span></div></td>
            <td>10/12/2026</td>
            <td>Rejected on 10/13</td>
            <td><a href="/test2">Link2</a></td>
        </tr>
        <tr>
            <td>
                <div class="tw-rounded-md">Spring 2026</div>
                <div class="tw-rounded-md">GRE Q 170</div>
                <div class="tw-rounded-md">International</div>
            </td>
        </tr>
        <tr>
            <td>Stanford</td>
            <td><div class="tw-text-gray-900"><span>Physics</span></div></td>
            <td>10/14/2026</td>
            <td>Waitlisted on 10/15</td>
            <td><a href="/test3">Link3</a></td>
        </tr>
        <tr>
            <td></td>
        </tr>
    </tbody>
    </html>
    '''
    
    resp1 = MagicMock(status_code=200, content=valid_html)
    resp2 = MagicMock(status_code=500)
    resp3 = requests.exceptions.RequestException("Timeout")
    resp4 = MagicMock(status_code=200, content=b"<html><body></body></html>")
    resp5 = KeyboardInterrupt()

    mock_session.get.side_effect = [resp1, resp2, resp3, resp4, resp5]
    
    data, seen, term, page = scrape(target_count=10, start_term_idx=0, start_page=1)
    
    assert len(data) == 3
    assert data[0]["University"] == "USC"
    assert data[1]["University"] == "MIT"
    assert data[2]["University"] == "Stanford"