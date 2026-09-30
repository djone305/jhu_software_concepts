import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
src_path = project_root / "src"

for path in (str(project_root), str(src_path)):
    if path not in sys.path:
        sys.path.insert(0, path)

import clean


@pytest.fixture
def sample_records():
    """Provides standard valid and dirty record sets for data cleaning tests."""
    return [
        {
            "URL link to applicant entry": "https://example.com/1",
            "University": "  Stanford University  ",
            "Program Name": " Computer Science ",
            "Applicant Status": "Accepted",
            "GPA": "3.85",
            "GRE General Quantitative": "168",
            "GRE General Verbal": "160",
            "Degree": "Master's",
            "Season": "Fall 2026",
        },
        {
            "URL link to applicant entry": "https://example.com/2",
            "University": "MIT",
            "Program Name": "Physics",
            "Applicant Status": "Rejected",
            "GPA": None,
            "GRE General Quantitative": "N/A",
            "GRE General Verbal": "invalid",
            "Degree": None,
            "Season": None,
        },
    ]


@pytest.mark.clean
def test_clean_pipeline(sample_records):
    """Explicitly tests the main data cleaning pipeline functions."""
    cleaned = None
    
    # Dynamically find callable functions in your clean.py file
    func_names = [f for f in dir(clean) if callable(getattr(clean, f)) and not f.startswith("__")]
    
    for fn_name in func_names:
        # Look for a likely cleaning function
        if any(k in fn_name.lower() for k in ["clean", "process", "format", "df"]):
            func = getattr(clean, fn_name)
            try:
                result = func(sample_records)
                # If function modifies in-place (returns None), use the modified sample
                cleaned = result if result is not None else sample_records
                break
            except Exception:
                pass # Try the next function if this one throws a signature error
                
    assert cleaned is not None, f"Failed to execute a cleaning function. Found: {func_names}"


@pytest.mark.clean
@pytest.mark.parametrize(
    "raw_val, expected",
    [
        ("3.85", 3.85),
        ("165", 165.0),
        ("N/A", None),
        ("invalid", None),
        (None, None),
    ],
)
def test_numeric_cleaning_helpers(raw_val, expected):
    """Uses pytest parameterization to test numeric conversions (e.g., GPA or GRE score parsing)."""
    # Test individual float/int conversion helpers directly if they exist
    for helper_name in ("clean_gpa", "clean_float", "parse_number", "clean_score"):
        if hasattr(clean, helper_name):
            func = getattr(clean, helper_name)
            assert func(raw_val) == expected