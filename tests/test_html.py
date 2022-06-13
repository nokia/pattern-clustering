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

from pattern_clustering import colors_to_html, html, make_html_colors, clustered_lines_to_html

def test_make_html_colors():
    for n in range(1, 5):
        colors = make_html_colors(n)
        assert len(colors) == n

def test_colors_to_html():
    colors = make_html_colors(5)
    assert colors_to_html(colors, i_to_label = lambda i: f"color {i}")

def test_clustered_lines_to_html():
    num_clusters = 2
    num_lines = 5
    assert clustered_lines_to_html(
        [
            f"line{i}"
            for i in range(num_lines)
        ],
        {
            i : i % num_clusters
            for i in range(num_lines)
        },
        show_caption=True,
        map_cluster_name={
            k : f"cluster {k % num_clusters}"
            for k in range(num_clusters)
        }
    )
