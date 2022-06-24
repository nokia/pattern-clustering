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
from pybgl.ipynb import in_ipynb, ipynb_display_graph
from pattern_clustering import *

NAMES = ["float", "int", "ipv4", "spaces", "uint"]
MAP_NAME_DFA = make_map_name_dfa(MAP_NAME_RE, NAMES)

def test_pattern_automaton_largest():
    w = "11.22.33.44 55.66 789"
    for (make_mg, num_vertices_expected, num_edges_expected) in [
        (MultiGrepFunctorLargest, 14, 26)
    ]:
        g = PatternAutomaton(w, MAP_NAME_DFA, make_mg)
        assert initial(g) == 0
        assert is_final(len(w), g)
        assert num_vertices(g) == num_vertices_expected, f"{pformat(locals())}"
        assert num_edges(g) == num_edges_expected, f"{pformat(locals())}"

def test_pattern_automaton_empty_word():
    w = ""
    g = PatternAutomaton(w, MAP_NAME_DFA)
    assert num_vertices(g) == 1
    assert num_edges(g) == 0
    assert is_final(0, g)

def test_pattern_automaton_equals():
    g1 = PatternAutomaton("11.22.33.44 55.66 789", MAP_NAME_DFA)
    g2 = PatternAutomaton("55.66.77.88 9876 55.44", MAP_NAME_DFA)
    g3 = PatternAutomaton("1.2.3.4 77.88 90", MAP_NAME_DFA)
    assert g1 != g2
    assert g1 == g3

def test_pattern_automaton_get_slice():
    NAMES = ["float", "int", "ipv4", "spaces", "uint"]
    MAP_NAME_DFA = make_map_name_dfa(MAP_NAME_RE, NAMES)

    w = "10   abc  1.2.3.4  de 56.78"
    g = PatternAutomaton(w, MAP_NAME_DFA, MultiGrepFunctorLargest)
    types = {label(e, g) for e in sorted(edges(g))}
    expected = {"ipv4", "int", "float", "any", "spaces", "uint"}
    assert types == expected
    obtained = {g.get_slice(e) for e in sorted(edges(g))}
    if in_ipynb():
        ipynb_display_graph(g)
    expected = {
        (0, 2),    # float, int, uint
        (2, 5),    # spaces
        (5, 8),    # any
        (8, 10),   # spaces
        (10, 11),  # int, uint
        (11, 12),  # any
        (12, 13),  # int, uint
        (10, 13),  # float
        (13, 14),  # any
        (14, 15),  # int, uint
        (12, 15),  # float
        (15, 16),  # any
        (16, 17),  # int, uint
        (14, 17),  # float
        (17, 19),  # spaces
        (19, 21),  # any
        (21, 22),  # spaces
        (22, 24),  # uint, int
        (24, 25),  # any
        (25, 27),  # int, uint
        (22, 27),  # float
        (10, 17),  # ipv4
    }
    assert obtained == expected, f"get_slices: {pformat(locals())}"
    obtained = {g.get_infix(e) for e in sorted(edges(g))}
    expected = {
        "1", "2", "3", "4", "10", "56", "78", #int, uint
        ".", "abc", "de", # any
        " ", "  ", "   ", # spaces
        "1.2.3.4",  # ipv4
        "1.2", "2.3", "3.4", "56.78",  # float
    }
    assert obtained == expected, f"get_infix: {pformat(locals())}"
