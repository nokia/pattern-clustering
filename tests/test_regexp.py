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

from pybgl.automaton import accepts
from pattern_clustering.regexp import *


def test_make_dfa_any():
    g = make_dfa_any()
    assert accepts("abc123", g)
    assert not accepts("abc de 123", g)
    assert not accepts("abc\t123", g)
    assert accepts("#!~@", g)

def test_re_0_n():
    map_max_re = {
        32 : RE_0_32,
        128 : RE_0_128,
        255 : RE_0_255,
    }
    for (n, regexp) in map_max_re.items():
        g = compile_dfa(regexp)
        for i in range(n + 1):
            print(i, n, regexp)
            assert accepts(str(i), g)
        assert not accepts("-1", g)
        assert not accepts(str(n+1), g)

def test_re_alnum():
    g = compile_dfa(RE_ALNUM)
    assert accepts("0", g)
    assert accepts("12", g)
    assert not accepts("-123", g)
    assert accepts("abc", g)
    assert accepts("x0y1z", g)

def test_re_delimiters():
    g = compile_dfa(RE_DELIMITER)
    assert accepts("---", g)
    assert accepts("======", g)

def test_re_hexa():
    g = compile_dfa(RE_HEXA)
    assert accepts("0", g)
    assert accepts("12", g)
    assert not accepts("-123", g)
    assert not accepts("+123", g)
    assert accepts("aa1234ff", g)
    assert not accepts("aa1234ffx", g)

def test_re_float():
    g = compile_dfa(RE_FLOAT)
    assert accepts("1", g)
    assert accepts("1.2", g)
    assert accepts("12.34", g)
    assert accepts("-12.34", g)
    assert not accepts(".34", g)
    assert not accepts("12.", g)

def test_re_int():
    g = compile_dfa(RE_INT)
    assert accepts("0", g)
    assert accepts("12", g)
    assert accepts("-123", g)
    assert accepts("+123", g)
    assert not accepts("123.4", g)

def test_re_ipv4():
    g = compile_dfa(RE_IPV4)
    assert accepts("192.168.0.255", g)
    assert accepts("190.068.0.255", g)
    assert accepts("0.0.0.0", g)
    assert accepts("255.255.255.255", g)
    assert not accepts("256.0.0.0", g)
    assert not accepts("0.256.0.0", g)
    assert not accepts("0.0.256.0", g)
    assert not accepts("0.0.0.256", g)

def test_re_ipv6():
    g = compile_dfa(RE_IPV6)
    assert accepts("::1", g)
    assert accepts("2a02:a802:23::1", g)
    assert accepts("2a01:e35:2e49:10c0:eeb3:6f16:6bd4:d833", g)
    assert accepts("2A01:E35:2E49:10C0:EEB3:6F16:6BD4:D833", g)
    assert not accepts("2A01:X35:2E49:10C0:EEB3:6F16:6BD4:D833", g)
    assert not accepts(":", g)
    assert not accepts("A", g)
    assert not accepts(":A", g)
    assert not accepts("1", g)
    assert not accepts(":1", g)

def test_re_net_ipv4():
    g = compile_dfa(RE_NET_IPV4)
    assert accepts("0.0.0.0", g) is False
    assert accepts("0.0.0.0/0", g) is True
    assert accepts("192.168.1.0/24", g) is True
    assert accepts("192.168.1.183/32", g) is True
    assert accepts("192.168.1.256/32", g) is False
    assert accepts("192.168.1.183/33", g) is False

def test_re_net_ipv6():
    g = compile_dfa(RE_NET_IPV6)
    assert accepts("2a02:a802:23::1", g) is False
    assert accepts("2a02:a802:23::1/44", g) is True
    assert accepts("2a02:a802:23::1/128", g) is True
    assert accepts("2a02:a802:23::1/0", g) is True
    assert accepts("2A02:A802:23::1/128", g) is True
    assert accepts("2x02:a802:23::1/128", g) is False
    assert accepts("2a02:a802:23::1/129", g) is False

def test_re_path():
    g = compile_dfa(RE_PATH)
    assert not accepts("aaa/bbb", g)
    assert accepts("/aaa/bbb", g)
    assert accepts("/my_folder0/my-subdir1", g)

def test_re_spaces():
    g = compile_dfa(RE_SPACES)
    assert accepts("  ", g)
    assert accepts("  \t  ", g)
    assert not accepts(" x \t y ", g)

def test_re_word():
    g = compile_dfa(RE_WORD)
    assert accepts("abc", g)
    assert not accepts("abc de", g)
    assert accepts("12", g)

def test_re_uint():
    g = compile_dfa(RE_UINT)
    assert accepts("0", g)
    assert accepts("12", g)
    assert not accepts("-123", g)
    assert not accepts("+123", g)
    assert not accepts("123.4", g)

def test_make_map_name_dfa():
    NAMES = ["int", "float", "ipv4"]
    MAP_NAME_DFA = make_map_name_dfa(MAP_NAME_RE, NAMES)
    assert set(MAP_NAME_DFA.keys()) == set(NAMES)
