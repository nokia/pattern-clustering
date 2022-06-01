#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

__author__ = "Marc-Olivier Buob"
__maintainer__ = "Marc-Olivier Buob"
__email__ = "marc-olivier.buob@nokia-bell-labs.com"
__copyright__ = "Copyright (C) 2022, Nokia"
__license__ = "Nokia"

from collections        import defaultdict
from pybgl.property_map import ReadPropertyMap, make_func_property_map

def make_html_colors(num_colors :int, s :str = "80%", l :str = "40%") -> list:
    """
    Make a list of `num_colors` colors scattered over the rainbow gradient.
    Args:
        num_colors: `int` indicating the number of
        s: `str` containing the saturation (cf HSL).
        l: `str` containing the light (cf HSL).
    Returns:
        A `list(str)` made of `num_colors` HTML colors.
    """
    assert num_colors > 0
    return [
        "hsl(%s)" % ", ".join([str(int(360 * (i / num_colors))), s, l])
        for i in range(num_colors)
    ]


def values_to_colors(values, *cls, **kwargs) -> dict:
    unique_values = set(values)
    colors = make_html_colors(len(unique_values), *cls, **kwargs)
    return {
        value : colors[i]
        for (i, value) in enumerate(sorted(unique_values))
    }


def colors_to_html(colors :list, i_to_label, join :str = "&nbsp;"):
    """
    Export a list of HTML colors to HTML strings.
    Args:
        colors: A `list(str)` containing HTML colors.
        i_to_label: `Callback(int) -> str` returning the label corresponding
            to a given color index (according to `colors`).
        join: `str` used to join HTML strings related to each color.
    Returns:
        The corresponding HTML `str` instance.
    """
    return "&nbsp;".join([
        "<font style='color:%s'>%s</font>" % (color, i_to_label(i))
        for (i, color) in enumerate(colors)
    ])


class RowFormatter:
    """
    Fonctor used to format row (line number) of a file.
    """
    def __init__(self, pmap_color :ReadPropertyMap = None, fmt_row :str = "%3s"):
        """
        Constructor.
        Args:
            pmap_color: `ReadPropertyMap{int : str}` mapping a row with
                its corresponding color.
            fmt_row: Format `str` to display the row.
        """
        self.pmap_color = pmap_color
        self.fmt_row = fmt_row


    def __call__(self, row :int, line :str) -> str:
        """
        Callback operator.
        Args:
            row: `int` corresponding to the current row (line number).
            line: `str` containing the current line.
        Returns:
            The corresponding HTML row label.
        """
        color = self.pmap_color[row] if self.pmap_color else None
        row_label = self.fmt_row % row
        return (
            "<font style='color:%s'>%s</font>" % (color, row_label) if color \
            else row_label
        )


def clusters_to_row_formatter(
    map_row_cluster :dict,
    map_cluster_color :dict
) -> RowFormatter:
    return RowFormatter(
        make_func_property_map(
            lambda row: map_cluster_color.get(map_row_cluster.get(row))
        )
    )


def lines_to_html(
    lines        :list,
    skip_line    :callable = None,
    line_to_html :callable = None
) -> str:
    """
    Export a list of `str` to HTML.
    Args:
        lines: A `list(str)` containing the considered `str` (e.g. the
            lines of a given input file).
        skip_line: `Callback(int, str) -> bool` taking in parameters the row
            and the line content, and returning `True` if the line is relevant.
            By default, all lines are considered.
        line_to_html: `Callback(int, str) -> str` taking in parameters
            the row (line number) and the line content, and returning the
            corresponding HTML rendering.
    Returns:
        The corresponding HTML `str`.
    """
    if not skip_line:
        skip_line = lambda row, line: False
    if not line_to_html:
        line_to_html = lambda i, line: "%3s: %s" % (i, line)
    return "<pre>%s</pre>" % "<br/>".join([
        line_to_html(row, line)
        for (row, line) in enumerate(lines)
        if not skip_line(row, line)
    ])


def lines_to_html(
    lines        :list,
    skip_line    :callable = None,
    line_to_html :callable = None
) -> str:
    """
    Export a list of `str` to HTML.
    Args:
        lines: A `list(str)` containing the considered `str` (e.g. the
            lines of a given input file).
        skip_line: `Callback(int, str) -> bool` taking in parameters the row
            and the line content, and returning `True` if the line is relevant.
            By default, all lines are considered.
        line_to_html: `Callback(int, str) -> str` taking in parameters
            the row (line number) and the line content, and returning the
            corresponding HTML rendering.
    Returns:
        The corresponding HTML `str`.
    """
    if not skip_line:
        skip_line = lambda row, line: False
    if not line_to_html:
        line_to_html = lambda i, line: "%3s: %s" % (i, line)
    return "<pre>%s</pre>" % "<br/>".join([
        line_to_html(row, line)
        for (row, line) in enumerate(lines)
        if not skip_line(row, line)
    ])

def clustered_lines_to_html(
    lines            :list,
    map_row_cluster  :dict,
    row_to_html            = None,
    line_to_html           = None,
    skip_line              = None,
    show_caption     :bool = True,
    map_cluster_name :dict = None,
    display_by_cluster: bool = False,
) -> str:
    """
    Export a list of clustered `str` to HTML.
    Args:
        lines: A `list(str)` containing the considered `str` (e.g. the
            lines of a given input file).
        map_row_cluster: A `dict(int, Cluster)` mapping each row.
        row_to_html: `Callback(int, str) -> str` mapping
            the row (line number) and the line content with the
            corresponding HTML rendering of the line.
            See also `siva.html.RowFormatter`.
        line_to_html: `Callback(int, str) -> str` mapping
            the row (line number) and the line content with the
            corresponding HTML rendering of the line.
        skip_line: `Callback(int, str) -> bool` taking in parameters the row
            and the line content, and returning `True` if the line is relevant.
            By default, all lines are considered.
        show_caption: Pass `True` to display the caption mapping each
            cluster with its corresponding color.
        map_cluster_name: `dict{Cluster : str}` mapping each `Cluster` with its name.
    Returns:
        The corresponding HTML `str`.
    """
    clusters = set(map_row_cluster.values())
    map_cluster_color = values_to_colors(clusters)

    if skip_line is None:
        skip_line = lambda row, line: False
    if not row_to_html:
        row_to_html = clusters_to_row_formatter(map_row_cluster, map_cluster_color)
    if not line_to_html:
        line_to_html = lambda row, line: line
    cluster_colors = [
        color
        for color in map_cluster_color.values()
    ]

    if not map_cluster_name:
        map_cluster_name = {
            cluster : "Cluster %d" % i
            for (i, cluster) in enumerate(clusters)
        }
    cluster_names = [
        map_cluster_name[cluster]
        for cluster in clusters
    ]

    return "".join([
        # Caption
        colors_to_html(
            cluster_colors,
            lambda i: cluster_names[i],
            join = "&nbsp;"
        ) if show_caption else "",
        # Lines
        lines_to_html(
            lines,
            skip_line = skip_line,
            line_to_html = lambda row, line: "%s: %s" % (
                row_to_html(row, line),
                line_to_html(row, line)
            )
        )
    ])

