import pytest
from unittest.mock import patch
from app import execute_etl_pipeline, task_status

@pytest.mark.web
@patch("app.run_scrape")
def test_execute_etl_pipeline_exception(mock_scrape):
    """Tests that the ETL pipeline safely catches and logs exceptions."""
    # Force the scraper to throw an error
    mock_scrape.side_effect = Exception("Simulated database crash")
    
    # Run the pipeline
    execute_etl_pipeline()
    
    # Assert the exception was caught and logged in task_status
    assert task_status["error"] == "Simulated database crash"
    assert task_status["is_running"] is False