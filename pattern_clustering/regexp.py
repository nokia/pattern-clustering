#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Marc-Olivier Buob"
__maintainer__ = "Marc-Olivier Buob"
__email__ = "marc-olivier.buob@nokia-bell-labs.com"
__copyright__ = "Copyright (C) 2020, Nokia"
__license__ = "Nokia"

from string import printable
from pybgl.automaton import Automaton, add_edge, set_final
from pybgl.regexp import compile_dfa


def make_re_hex_digit(lower_case: bool = True, upper_case: bool = True) -> str:
    return r"[0-9%s%s]" % (
        "a-f" if lower_case else "",
        "A-F" if upper_case else ""
    )


def make_re_ipv6(lower_case: bool = True, upper_case: bool = True) -> str:
    assert lower_case or upper_case
    hex4 = "[%s%s0-9]{0,4}" % (
        "a-f" if lower_case else "",
        "A-F" if upper_case else ""
    )
    ipv6_sep = ":"
    return "((" + hex4 + ")?(" + ipv6_sep + hex4 + ")+" + ipv6_sep + hex4 + ")"


# Avoid to use it (long to compile, long to compute language_density)
def make_re_ipv6_strict(*cls, **kwargs) -> str:
    re_seg = make_re_hex_digit(*cls, **kwargs) + r"{1,4}"
    return "(%s)" % "|".join([
        "(" + re_seg + ":){7,7}" + re_seg,  # 1:2:3:4:5:6:7:8
        "(" + re_seg + ":){1,7}:",  # 1::                                 1:2:3:4:5:6:7::
        "(" + re_seg + ":){1,6}:" + re_seg,  # 1::8               1:2:3:4:5:6::8   1:2:3:4:5:6::8
        "(" + re_seg + ":){1,5}(:" + re_seg + "){1,2}",  # 1::7:8             1:2:3:4:5::7:8   1:2:3:4:5::8
        "(" + re_seg + ":){1,4}(:" + re_seg + "){1,3}",  # 1::6:7:8           1:2:3:4::6:7:8   1:2:3:4::8
        "(" + re_seg + ":){1,3}(:" + re_seg + "){1,4}",  # 1::5:6:7:8         1:2:3::5:6:7:8   1:2:3::8
        "(" + re_seg + ":){1,2}(:" + re_seg + "){1,5}",  # 1::4:5:6:7:8       1:2::4:5:6:7:8   1:2::8
        re_seg + ":((:" + re_seg + "){1,6})",  # 1::3:4:5:6:7:8     1::3:4:5:6:7:8   1::8
        ":((:" + re_seg + "){1,7}|:)",  # ::2:3:4:5:6:7:8    ::2:3:4:5:6:7:8  ::8       ::
        # fe80::7:8%eth0 fe80::7:8%1  (link-local IPv6 addresses with zone index)
        "fe80:(:" + re_seg + "){0,4}%[0-9a-zA-Z]{1,}",
        # ::255.255.255.255  ::ffff:255.255.255.255  ::ffff:0:255.255.255.255
        # (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
        "::(ffff(:0{1,4}){0,1}:){0,1}" + RE_IPV4,
        #  2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
        "(re_seg:){1,4}:" + RE_IPV4
    ])


RE_0_32 = r"(3[0-2]|[0-2]?[0-9])"
RE_0_128 = r"(12[0-8]|1[0-1][0-9]|([0-9]{1,2}))"
RE_0_255 = r"(25[0-5]|(2[0-4]|[0-1]{0,1}[0-9]){0,1}[0-9])"
RE_ALNUM = r"[a-zA-Z0-9]+"
RE_ANY = r"(\S|\s)+"  # The metacharacter "." is not yet supported in pybgl
RE_BOOL = r"0|1"
RE_DELIMITER = r"[-+=*@~#]+"
RE_SIGN = r"(-|[+])?"
RE_UINT = r"[0-9]+"
RE_INT = RE_SIGN + RE_UINT
RE_GENERAL_INT = RE_SIGN + r"[0-9]{1,3}(,[0-9]{3})*"
RE_FLOAT = RE_SIGN + RE_UINT + r"([.]" + RE_UINT + ")?"
RE_APPROX_FLOAT = "~?" + RE_FLOAT
RE_HEXA = make_re_hex_digit() + r"+"
RE_IPV4 = r"((" + RE_0_255 + "[.]){3}" + RE_0_255 + ")"
RE_IPV6 = make_re_ipv6()  # make_re_ipv6_strict()
RE_LETTERS = r"[a-zA-Z]+"
RE_NET_IPV4 = "/".join([RE_IPV4, RE_0_32])
RE_NET_IPV6 = "/".join([RE_IPV6, RE_0_128])
RE_PATH = r"(/[-/:._a-zA-Z0-9]+)"
RE_SPACES = r"\s+"
RE_WORD = r"\S+"

MAP_NAME_RE = {
    "alnum": RE_ALNUM,
    "any": RE_ANY,
    "approx_float": RE_APPROX_FLOAT,
    "bool": RE_BOOL,
    "delimiter": RE_DELIMITER,
    "float": RE_FLOAT,
    "general_int": RE_GENERAL_INT,
    "hexa": RE_HEXA,
    "int": RE_INT,
    "ipv4": RE_IPV4,
    "ipv6": RE_IPV6,
    "letters": RE_LETTERS,
    "net_ipv4": RE_NET_IPV4,
    "net_ipv6": RE_NET_IPV6,
    "path": RE_PATH,
    "uint": RE_UINT,
    "spaces": RE_SPACES,
    "word": RE_WORD,
}


def get_pattern_names() -> list:
    return list(MAP_NAME_RE.keys())


def make_map_name_dfa(names=None, map_name_re: dict = None) -> dict:
    if map_name_re is None:
        map_name_re = MAP_NAME_RE
    map_name_dfa = dict()
    for name in names:
        try:
            regex = map_name_re[name]
            map_name_dfa[name] = compile_dfa(regex)
        except Exception as e:
            raise Exception("Error when processing %r: %s" % (name, e))
    return map_name_dfa


def make_dfa_empty() -> Automaton:
    dfa_empty = Automaton(1)
    set_final(0, dfa_empty, False)
    return dfa_empty


def make_dfa_any(alphabet: iter = None, separator_alphabet: iter = None) -> Automaton:
    if not alphabet:
        alphabet = set(printable)
    if not separator_alphabet:
        separator_alphabet = {" ", "\t", "\n"}
    # return plus(bracket([a for a in alphabet - separator_alphabet]))
    dfa_any = Automaton(2)
    set_final(1, dfa_any)
    for a in set(alphabet) - set(separator_alphabet):
        add_edge(0, 1, a, dfa_any)
        add_edge(1, 0, a, dfa_any)
    return dfa_any
