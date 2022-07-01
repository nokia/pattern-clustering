#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

"""Top-level package for Pattern clustering."""

__author__     = "Marc-Olivier Buob, Maxime Raynal"
__maintainer__ = "Marc-Olivier Buob, Maxime Raynal"
__email__      = "marc-olivier.buob@nokia-bell-labs.com, maxime.raynal@nokia.com"
__copyright__  = "Copyright (C) 2022, Nokia"
__license__    = "BSD-3"
__version__ = '1.0.0'  # Use single quotes for bumpversion (see setup.cfg)

from .boost import *
from .html import *
from .language_density import *
from .multi_grep import *
from .pattern_automaton import *
from .regexp import *
