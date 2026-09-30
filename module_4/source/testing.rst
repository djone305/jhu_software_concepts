==============
Testing Guide
==============

All test code resides under the ``tests/`` directory. Tests are executed using ``pytest``.

Running the Tests
-----------------

To run the complete test suite with coverage:

.. code-block:: bash

   pytest -v --cov=src

Running Marked Tests
--------------------

Custom Pytest markers allow execution of specific test subsets:

.. code-block:: bash

   # Run only database integration tests
   pytest -m db

   # Run only Flask UI/page tests
   pytest -m ui

   # Exclude end-to-end integration tests
   pytest -m "not integration"

Expected DOM Selectors (UI Testing)
-----------------------------------

UI tests in ``tests/test_buttons.py`` and ``tests/test_flask_page.py`` validate the presence of specific HTML elements:

===================  =======================  ======================================================
Page Route           Selector                 Expected Element / Behavior
===================  =======================  ======================================================
``/``                ``table#analysis-table`` Analysis table containing summary metrics
``/``                ``form#filter-form``     Form containing dropdowns for university/program filter
``/``                ``button#submit-btn``    Filter submission button
``/index``           ``div.alert-info``       Status message display area
===================  =======================  ======================================================

Fixtures & Test Doubles
-----------------------

The test suite in ``tests/conftest.py`` provides key fixtures and test doubles:

* **``flask_app``**: Yields a Flask test application initialized in testing mode (``TESTING=True``).
* **``client``**: Exposes a Flask test client for executing simulated GET/POST requests without running a live HTTP server.
* **``db_session``**: Provides an isolated, transactional SQLAlchemy session connected to the test database that automatically rolls back changes after each test.
* **``mock_scraped_data``**: Returns sample uncleaned records for unit testing ``clean.py`` parsing logic without invoking web requests.