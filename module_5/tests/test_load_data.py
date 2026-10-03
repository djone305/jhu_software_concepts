import sys
import os
import importlib
from unittest.mock import patch
import pytest

@pytest.mark.load_data
@pytest.mark.db
def test_load_data_missing_db_password(monkeypatch):
    """Verify ValueError is raised when DB_PASSWORD is not set."""
    # 1. Clear environment variables
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.setenv("DB_PASSWORD", "")

    # 2. Unload load_data AND any module that reads environment variables (e.g. models/config)
    for mod_name in list(sys.modules.keys()):
        if "load_data" in mod_name or "models" in mod_name or "config" in mod_name:
            sys.modules.pop(mod_name, None)

    # 3. Patch load_dotenv to prevent reading local .env file
    with patch("dotenv.load_dotenv", return_value=False), \
         patch.dict(os.environ, {}, clear=True):
        
        with pytest.raises(ValueError, match="(?i)missing database password"):
            import src.load_data as ld
            importlib.reload(ld)
            
            # If validation is inside a function, execute it:
            if hasattr(ld, "get_db_password"):
                ld.get_db_password()
            elif hasattr(ld, "load_scraped_data_to_db"):
                ld.load_scraped_data_to_db([])