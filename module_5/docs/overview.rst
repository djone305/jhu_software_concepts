===================
Overview & Setup
===================

This project extracts, cleans, loads, and analyzes applicant data from GradCafe into a PostgreSQL database, providing a Flask web front-end for interactive data exploration.

Quickstart & Setup
-------------------

1. **Clone & Navigate to Module Folder**:

   .. code-block:: bash

      cd module_4

2. **Set Up Virtual Environment**:

   .. code-block:: bash

      python -m venv .venv
      source .venv/bin/activate  # On Windows: .venv\Scripts\activate
      pip install -r requirements.txt

3. **Configure Environment Variables**:

   Create a ``.env`` file inside ``src/`` (or set system environment variables) with the following required parameters:

   .. code-block:: ini

      DB_USER=postgres
      DB_PASSWORD=postgrespassword
      DB_HOST=localhost
      DB_PORT=5432
      DB_NAME=gradcafe_db
      DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/gradcafe_db
      SECRET_KEY=dev-secret-key

Required Environment Variables
------------------------------

================  ======================================================  =============================================================
Variable          Description                                             Example Value
================  ======================================================  =============================================================
``DB_USER``       PostgreSQL username                                     ``postgres``
``DB_PASSWORD``   PostgreSQL password                                     ``postgrespassword``
``DB_HOST``       PostgreSQL host address                                 ``localhost``
``DB_PORT``       PostgreSQL connection port                              ``5432``
``DB_NAME``       Target database name                                    ``gradcafe_db``
``DATABASE_URL``  Full SQLAlchemy connection string                       ``postgresql://postgres:postgrespassword@localhost:5432/gradcafe_db``
``SECRET_KEY``    Flask app session signing key                           ``your-secret-key``
================  ======================================================  =============================================================

Running the Web Application
---------------------------

Start the Flask development server:

.. code-block:: bash

   python src/app.py

Access the web portal at ``http://127.0.0.1:5000``.