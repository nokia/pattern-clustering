#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

__author__ = "Marc-Olivier Buob, Maxime Raynal"
__maintainer__ = "Marc-Olivier Buob, Maxime Raynal"
__email__ = "marc-olivier.buob@nokia-bell-labs.com, maxime.raynal@nokia.com"
__copyright__ = "Copyright (C) 2022, Nokia"
__license__ = "Nokia"

from pattern_clustering.regexp import make_map_name_dfa
from pattern_clustering.pattern_automaton import *

NAMES = ["float", "int", "ipv4", "spaces", "uint"]
MAP_NAME_DFA = make_map_name_dfa(NAMES)

def test_pattern_automaton():
    w = "11.22.33.44 55.66 789"
    g = PatternAutomaton(w, MAP_NAME_DFA)
    assert initial(g) == 0
    assert is_final(len(w), g)
    assert num_vertices(g) == 6
    assert num_edges(g) == 7

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
    w = "10   abc  1.2.3.4  de 56.78"
    g = PatternAutomaton(w, MAP_NAME_DFA)
    types = {label(e, g) for e in sorted(edges(g))}
    expected = {"ipv4", "int", "float", "any", "spaces", "uint"}
    assert types == expected
    slices = [g.get_slice(e) for e in sorted(edges(g))]
    expected = [
        (0, 2),    # float
        (0, 2),    # int
        (0, 2),    # uint
        (2, 5),    # spaces
        (5, 8),    # any
        (8, 10),   # spaces
        (10, 17),  # ipv4
        (17, 19),  # spaces
        (19, 21),  # any
        (21, 22),  # spaces
        (22, 27)   # float
    ]
    assert slices == expected
    obtained = [g.get_infix(e) for e in sorted(edges(g))]
    print(obtained)
    expected = [
        "10",       # float
        "10",       # int
        "10",       # uint
        "   ",      # spaces
        "abc",      # any
        "  ",       # spaces
        "1.2.3.4",  # ipv4
        "  ",       # spaces
        "de",       # any
        " ",        # spaces
        "56.78"     # float
    ]
    assert obtained == expected
