import os, sys
sys.path.insert(0, os.path.abspath(".."))  # make your package importable
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",           # Google / NumPy style docstrings
    "sphinx_autodoc_typehints",
]
autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True
