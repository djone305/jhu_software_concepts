====================
System Architecture
====================

The application uses a 3-tier modular architecture separating Data Extraction/Transformation, Persistent Storage, and Web Presentation.

.. code-block:: text

   +-----------------------------------------------------------------------+
   |                             Web Layer                                 |
   |              Flask Application (app.py / UI Templates)                |
   +-----------------------------------+-----------------------------------+
                                       |
                                       v
   +-----------------------------------+-----------------------------------+
   |                             ETL Layer                                 |
   |   Scraper (scrape.py) -> Cleaner (clean.py) -> Loader (load_data.py)  |
   +-----------------------------------+-----------------------------------+
                                       |
                                       v
   +-----------------------------------+-----------------------------------+
   |                          Database Layer                               |
   |           PostgreSQL + SQLAlchemy ORM models (models.py)               |
   +-----------------------------------------------------------------------+

Layer Responsibilities
----------------------

1. **ETL Layer (Extract, Transform, Load)**
   * **Extract (``scrape.py``)**: Scrapes raw applicant entries from GradCafe using pagination and search query partitioning.
   * **Transform (``clean.py``)**: Standardizes raw scraped strings, parses decision dates, normalizes GPA/GRE scores, and handles missing fields.
   * **Load (``load_data.py``)**: Bulk-inserts transformed records into PostgreSQL using SQLAlchemy sessions while preventing duplicate entries.

2. **Database Layer (``models.py``)**
   * Utilizes **SQLAlchemy ORM** to manage relational schema mapping.
   * Maintains table definitions (e.g., ``Applicant``) and exposes connection session factories (``SessionLocal``).

3. **Web & Analytics Layer (``app.py``, ``query_data.py``, ``orm_queries.py``)**
   * **Flask Backend**: Serves web routes, renders data tables, handles filtering forms, and provides RESTful endpoints.
   * **Query Modules**: Executes aggregated analytical queries against PostgreSQL to compute acceptance rates, average GPAs, and decision timelines.