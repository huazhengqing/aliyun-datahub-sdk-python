# -*- coding: utf-8 -*-
#
# PyDatahub documentation build configuration file, created by
# sphinx-quickstart on Sat Feb  4 14:54:19 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import os
import sys

dirname = os.path.dirname

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, dirname(dirname(dirname(os.path.abspath(__file__)))))

# on_rtd is whether we are on readthedocs.org, this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.todo',
              'sphinx.ext.mathjax',
              'sphinx.ext.ifconfig',
              'sphinx.ext.viewcode',
              'sphinx.ext.autosummary',
              'sphinx.ext.napoleon']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of resources filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'PyDatahub'
copyright = u'1999-2017, The Alibaba Group Holding Ltd'
author = u'andy.xs'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
from datahub import __version__

version = __version__
# The full version, including alpha/beta/rc tags.
release = __version__

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to resources directory, that match files and
# directories to ignore when looking for resources files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = '_static/PyDatahub.png'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'PyDatahubdoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    'papersize': 'a4paper',

    # The font size ('10pt', '11pt' or '12pt').
    #'pointsize': '12pt',

    'classoptions': ',english',
    'inputenc': '',
    'utf8extra': '',

    # Additional stuff for the LaTeX preamble.
    'preamble': '''
        \usepackage{xeCJK}
        \usepackage{indentfirst}
        \setlength{\parindent}{2em}
        \setCJKmainfont[BoldFont=SimHei, ItalicFont=STKaiti]{SimSun}
        \setCJKmonofont[Scale=0.9]{Consolas}
        \setCJKfamilyfont{song}[BoldFont=SimSun]{SimSun}
        \setCJKfamilyfont{sf}[BoldFont=SimSun]{SimSun}
    '''
}

# Grouping the document tree into LaTeX files. List of tuples
# (resources start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'PyDatahub.tex', u'PyDatahub Documentation',
     u'The Alibaba Group Holding Ltd', 'manual'),
]

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (resources start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'pydatahub', u'PyDatahub Documentation',
     [author], 1)
]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (resources start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'PyDatahub', u'PyDatahub Documentation',
     author, 'PyDatahub', 'One line description of project.',
     'Miscellaneous'),
]

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'https://docs.python.org/': None}

mathjax_path = "https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"