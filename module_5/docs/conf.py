import os
import sys

# Tell Sphinx to go up one directory and look inside /src to find your Python files
sys.path.insert(0, os.path.abspath('../src'))

project = 'Grad Cafe ETL Pipeline'
copyright = '2026, Donnell'
author = 'Donnell'

# Enable autodoc to pull docstrings, napoleon to read them cleanly, and a modern UI theme
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']