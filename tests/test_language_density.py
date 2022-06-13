#!/usr/bin/env pytest
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

__author__ = "Marc-Olivier Buob, Maxime Raynal"
__maintainer__ = "Marc-Olivier Buob, Maxime Raynal"
__email__ = "marc-olivier.buob@nokia-bell-labs.com, maxime.raynal@nokia.com"
__copyright__ = "Copyright (C) 2022, Nokia"
__license__ = "Nokia"

from pprint import pformat
from pattern_clustering import PatternAutomaton, language_density, make_map_name_dfa

def test_language_density():
    names = ["float", "int", "ipv4", "spaces", "uint"]
    map_name_dfa = make_map_name_dfa(names)
    map_name_expected = {
        "float": 0.053171883656509704,
        "int": 0.053157894736842064,
        "ipv4": 9.519316254727908e-13,
        "spaces": 0.010101010101010102,
        "uint": 0.05263157894736826,
    }
    map_name_obtained = dict()
    for (name, g) in map_name_dfa.items():
        if name in map_name_expected:
            map_name_obtained[name] = language_density(g)
    assert map_name_obtained == map_name_expected, f"test_language_density: {pformat(locals())}"
