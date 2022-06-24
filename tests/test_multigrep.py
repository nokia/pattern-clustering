#!/usr/bin/env pytest
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

__author__     = "Maxime Raynal, Marc-Olivier Buob"
__maintainer__ = "Maxime Raynal, Marc-Olivier Buob"
__email__      = "{maxime.raynal,marc-olivier.buob}@nokia.com"
__copyright__  = "Copyright (C) 2020, Nokia"
__license__    = "Nokia"

from pattern_clustering.multi_grep    import *
from pattern_clustering.regexp        import MAP_NAME_RE, make_map_name_dfa

W = "1.2.3.4 5.6.7.8"
NAMES = ["int", "float", "ipv4"]
MAP_NAME_DFA = make_map_name_dfa(MAP_NAME_RE, NAMES)
assert set(MAP_NAME_DFA.keys()) == set(NAMES)

def test_multi_grep_all():
    fonctor = MultiGrepFunctorAll()
    multi_grep(W, MAP_NAME_DFA, fonctor)
    assert multi_grep_fonctor_to_dict(W, fonctor) == {
        "int"  : ["1", "2", "3", "4", "5", "6", "7", "8"],
        "float": ["1", "1.2", "2", "2.3", "3", "3.4", "4", "5", "5.6", "6", "6.7", "7", "7.8", "8"],
        "ipv4" : ["1.2.3.4", "5.6.7.8"],
    }

def test_multi_grep_largest():
    fonctor = MultiGrepFunctorLargest()
    multi_grep(W, MAP_NAME_DFA, fonctor)
    assert multi_grep_fonctor_to_dict(W, fonctor) == {
        "int"  : ["1", "2", "3", "4", "5", "6", "7", "8"],
        "float": ["1.2", "2.3", "3.4", "5.6", "6.7", "7.8"],
        "ipv4" : ["1.2.3.4", "5.6.7.8"],
    }

def test_multi_grep_patterns_delims():
    map_word_expected = {
        "!222aaa111zzb" : {
            "word" : [(0, 13)],
        },
        "111  zzz 22yy" : {
            "word"   : [(0, 3), (5, 8), (9, 13)],
            "int"    : [(0, 3)],
            "float"  : [(0, 3)],
        },
        "  111  zzz 22yy  " : {
            "word"   : [(2, 5), (7, 10), (11, 15)],
            "int"    : [(2, 5)],
            "float"  : [(2, 5)],
        },
        "toto: 3333" : {
            "word"   : [(0, 5), (6, 10)],
            "int"    : [(6, 10)],
            "float"  : [(6, 10)],
        }
    }

    names = ["word", "ipv4", "int", "float", "spaces"]
    separators = {"spaces"}
    map_name_dfa = make_map_name_dfa(MAP_NAME_RE, names)

    for (word, expected) in map_word_expected.items():
        functor = MultiGrepFunctorLargest()
        multi_grep_with_delimiters(
            word, map_name_dfa, functor,
            is_pattern_separator = lambda name: name in separators
        )
        indices = functor.indices()
        assert indices == expected
