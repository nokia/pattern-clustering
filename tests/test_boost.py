#!/usr/bin/env pytest
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

__author__     = "Marc-Olivier Buob"
__maintainer__ = "Marc-Olivier Buob"
__email__      = "marc-olivier.buob@nokia-bell-labs.com"
__copyright__  = "Copyright (C) 2020, Nokia"
__license__    = "Nokia"

from pprint import pformat
from pattern_clustering import *

def test_pattern_clustering_env():
    env = PatternClusteringEnv()
    assert env.map_name_dfa
    assert env.alphabet
    assert "any" in env.map_name_density
    assert env.map_name_density
    assert set(env.map_name_dfa) <= set(env.map_name_density)

def test_make_densities():
    map_name_density = {"a" : 0.1, "c" : 0.2, "b" : 0.3, "d" : 0.0}
    obtained = make_densities(map_name_density)
    expected = [0.1, 0.3, 0.2, 0.0]
    assert obtained == expected, f"{pformat(locals())}"

def test_make_pattern_automaton():
    map_name_dfa = make_map_name_dfa()
    w = "0.0.0.0         192.168.0.254   0.0.0.0         UG    600    0        0 wlp2s0"
    g1 = make_pattern_automaton_python(w, map_name_dfa)
    assert num_vertices(g1) == 41
    g2 = make_pattern_automaton(w, map_name_dfa)
    assert num_vertices(g2) == len(w) + 1
    assert num_edges(g1) == num_edges(g2) == 163

def test_pattern_distance():
    obtained = pattern_distance(
        "0.0.0.0         192.168.0.254   0.0.0.0         UG    600    0        0 wlp2s0",
        "192.168.0.0     0.0.0.0         255.255.255.0   U     600    0        0 wlp2s0",
        normalized = True
    )
    expected = 0.007259624900493844
    assert obtained == expected, f"{pformat(locals())}"
