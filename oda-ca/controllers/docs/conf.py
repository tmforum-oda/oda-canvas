# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'ODA-Component Accelerator'
copyright = '2021, TM Forum ODA-Component Accelerator project'
author = 'TM Forum ODA-Component Accelerator project'

# The full version, including alpha/beta/rc tags
release = 'v1alpha2'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'recommonmark']
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown'
}
# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
master_doc = 'index'

print('Copying README and image files')
import shutil
shutil.copy2('../README.md', '.') 
shutil.copy2('../componentOperator/README.md', './componentOperator') 
shutil.copy2('../componentOperator/sequenceDiagrams/componentOperator.png', './componentOperator/sequenceDiagrams') 
shutil.copy2('../apiOperatorSimpleIngress/README.md', './apiOperatorSimpleIngress') 
shutil.copy2('../apiOperatorSimpleIngress/sequenceDiagrams/apiOperatorSimpleIngress.png', './apiOperatorSimpleIngress/sequenceDiagrams') 
shutil.copy2('../securityController/README.md', './securityController') 
shutil.copy2('../securityController/sequenceDiagrams/securitySequenceKeycloak.png', './securityController/sequenceDiagrams') 
shutil.copy2('../securityController/sequenceDiagrams/securitySequenceKeycloakDetailed.png', './securityController/sequenceDiagrams') 
