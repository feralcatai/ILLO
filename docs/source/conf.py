# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
# Append (not insert) to avoid shadowing Python's standard library 'code' module
sys.path.append(os.path.abspath(os.path.join('..', '..')))

project = 'ILLO'
copyright = '2025, Charles Doebler'
author = 'Charles Doebler'
release = '2.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

templates_path = ['_templates']
exclude_patterns = []

# Mock CircuitPython hardware dependencies for documentation builds
# These modules require actual hardware and will fail during import on a regular PC
autodoc_mock_imports = [
    'adafruit_circuitplayground',
    'adafruit_ble',
    'ulab',
    'microcontroller',
    'storage',
    'simpleio',
    'board',
    'busio',
    'digitalio',
    'analogio',
    'audiobusio',
    'audiopwmio',
    'array',
]



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
