# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sio3pack

project = 'SIO3Pack'
copyright = '2025, Tomasz Kwiatkowski, Mateusz Masiarz, Jakub Rożek, Stanisław Struzik'
author = 'Tomasz Kwiatkowski, Mateusz Masiarz, Jakub Rożek, Stanisław Struzik'
release = sio3pack.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'autoapi.extension',
    'sphinx.ext.autodoc',  # Also required by AutoAPI.
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autoapi_dirs = ['../src/sio3pack/']

def should_skip_submodule(app, what, name, obj, skip, options):
    if what == "module":
        skip = True

    submodule = name.split(".")[-1]
    if submodule in ["migrations"]:
        skip = True
    return skip

def setup(sphinx):
    sphinx.connect("autoapi-skip-member", should_skip_submodule)

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
