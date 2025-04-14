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
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "special-members",
    "imported-members",
]
autoapi_dirs = ['../src/sio3pack/']
# Additional objects to include.
autoapi_include = [
    "sio3pack.django.common.handler.DjangoHandler",
    "sio3pack.django.sinolpack.handler.SinolpackDjangoHandler",
]
autodoc_typehints = 'description'

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
def should_skip_submodule(app, what, name, obj, skip, options):
    if what == "module":
        skip = True
    if what == "attribute":
        skip = True

    for object in autoapi_include:
        # Include everything from object.
        if name.startswith(object):
            skip = False
        # Include every parent modules.
        if object.startswith(name):
            skip = False

    submodule = name.split(".")[-1]
    # Don't show private objects.
    if submodule.startswith("_"):
        skip = True
    # Skip django migrations.
    if submodule in ["migrations"]:
        skip = True
    return skip

def setup(sphinx):
    sphinx.connect("autoapi-skip-member", should_skip_submodule)

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
