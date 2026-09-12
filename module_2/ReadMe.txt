Name: Donnell Jones djone305
Course: Modern Software Concepts in Python
Semester: Fall '26
Module 1 Assignment: Personal Website

Skills: Python, Flask, Bootstrap, Git/GitHub


Instructions:

To run this Flask website locally from the GitHub repository, follow the steps below.

Repository Link:
https://github.com/djone305/jhu_software_concepts

Steps to Clone and Run:

1. Clone the repository to your local machine using Git:
   git clone https://github.com/djone305/jhu_software_concepts.git

2. Navigate into the project repository and move into the module_1 folder:
   cd jhu_software_concepts/module_1

3. Create and activate a Python virtual environment:
   python -m venv venv
   venv\Scripts\activate

4. Install the required dependencies:
   pip install -r requirements.txt

5. Set the Flask application environment variable:
   set FLASK_APP=app   (Windows CMD)
   $env:FLASK_APP="app" (PowerShell)
   export FLASK_APP=app (Mac/Linux)

6. Run the local development server:
   python run.py

7. Open http://127.0.0.1:5000 in your web browser to view the site.