"""Sphinx configuration for PAL documentation."""

import os
import sys

# Add project root to path for autodoc
sys.path.insert(0, os.path.abspath("../.."))

# Project information
project = "PAL Framework"
copyright_info = "2025, Nicolas Iglesias"
author = "Nicolas Iglesias"
release = "0.0.2"

# Extensions
extensions = [
    "sphinx.ext.autodoc",  # Auto-generate docs from docstrings
    "sphinx.ext.napoleon",  # Support Google/NumPy style docstrings
    "sphinx.ext.viewcode",  # Add links to source code
    "sphinx.ext.intersphinx",  # Link to other projects' docs
    "sphinx.ext.doctest",  # Test code snippets in docs
    "sphinx.ext.coverage",  # Check docstring coverage
    "sphinx_autodoc_typehints",  # Add type hints to docs
    "myst_parser",  # Support Markdown files
    "sphinx_copybutton",  # Add copy button to code blocks
]

# Autodoc configuration
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": False,
    "exclude-members": "__weakref__",
    "show-inheritance": True,
}
autodoc_typehints = "both"
autodoc_typehints_format = "short"

# Napoleon settings for docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True

# MyST parser for Markdown support
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "html_image",
    "colon_fence",
    "smartquotes",
    "substitution",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

# HTML theme
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# Theme options
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
}

# Output file base name for HTML help builder
htmlhelp_basename = "PALdoc"

# LaTeX output
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
    "preamble": "",
    "fncychap": "\\usepackage[Bjornstrup]{fncychap}",
}

latex_documents = [
    ("index", "PAL.tex", "PAL Documentation", "Nicolas Iglesias", "manual"),
]

# Man page output
man_pages = [("index", "pal", "PAL Documentation", ["Nicolas Iglesias"], 1)]

# Texinfo output
texinfo_documents = [
    (
        "index",
        "PAL",
        "PAL Documentation",
        "Nicolas Iglesias",
        "PAL",
        "Prompt Assembly Language Framework",
        "Miscellaneous",
    ),
]

# Epub output
epub_title = project
epub_exclude_files = ["search.html"]

# Doctest configuration
doctest_global_setup = """
import asyncio
from pathlib import Path
from pal import *
"""

# Coverage extension settings
coverage_show_missing_items = True
coverage_statistics_to_report = True
coverage_statistics_to_stdout = True
