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

from siva.html import colors_to_html, html, make_html_colors, fill_colored_slices

def test_make_html_colors():
    for n in range(1, 5):
        colors = make_html_colors(n)
        assert len(colors) == n

def test_colors_to_html():
    colors = make_html_colors(5)
    html(colors_to_html(colors, i_to_label = lambda i: "color %d" % i))

def test_fill_colored_slices1():
    l = [(1, (0, 10)),]
    obtained = fill_colored_slices(l)
    expected = [
        (1, (0, 10)),
        (None, (10, None)),
    ]
    assert obtained == expected

def test_fill_colored_slices2():
    l = [(1, (5, 10)),]
    obtained = fill_colored_slices(l)
    expected = [
        (None, (0, 5)),
        (1, (5, 10)),
        (None, (10, None)),
    ]
    assert obtained == expected

def test_fill_colored_slices3():
    l = [
        (1, (10, 15)),
        (2, (20, 25))
    ]
    obtained = fill_colored_slices(l)
    expected = [
        (None, (0, 10)),
        (1, (10, 15)),
        (None, (15, 20)),
        (2, (20, 25)),
        (None, (25, None)),
    ]
    print(obtained)
    print(expected)
    assert obtained == expected
