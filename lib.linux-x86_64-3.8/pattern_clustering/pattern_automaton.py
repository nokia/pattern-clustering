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

from functools import partial
from pybgl.automaton import *
from pybgl.deterministic_inclusion import deterministic_inclusion
from pybgl.dijkstra_shortest_paths import dijkstra_shortest_path, make_path
from pybgl.property_map import make_assoc_property_map, make_func_property_map
from .multi_grep import MultiGrepFonctorUltimate, multi_grep

# PatternAutomaton may possibly drop some arcs, e.g. "spaces" arcs
class PatternAutomaton(Automaton):
    """
    A PatternAutomaton models a string at the pattern level using a automaton-like structure where each vertex
    corresponds to a string index; each arc corresponds to an infix and its corresponding pattern.
    """

    def __init__(
        self,
        word: str,
        map_name_dfa: dict,
        make_mg: callable = None,
        filtered_patterns=None
    ):
        """
        Constructs the `PatternAutomaton` related to an input words according
        to a collection of patterns and according to a `multi_grep` strategy.
        Args:
            word: An `str` instance.
            map_name_dfa: A `dict{str : Automaton}` mapping each relevant type with its
                corresponding `Automaton` instance.
            filtered_patterns: A subset (possibly empty) of `map_name_dfa.keys()` of type
                that must be caught my `multi_grep`, but not reflected as arcs in the
                `PatternAutomaton`. It can be used e.g. to drop spaces and get a smaller
                `PatternAutomaton`, but the position of spaces in the original lines will be lost.
        """
        if filtered_patterns is None:
            #  filtered_patterns = {"spaces"} # This will pose problem to transform PA to regexp
            filtered_patterns = set()
        if not make_mg:
            make_mg = MultiGrepFonctorUltimate
        mg = make_mg()

        # Add vertices
        n = len(word)
        super().__init__(n + 1)
        set_final(n, self)
        self.w = word

        # Add edges
        multi_grep(word, map_name_dfa, mg)
        if mg.indices():
            vertices_with_successors = set()
            vertices_with_predecessors = set()
            for (name, jks) in mg.indices().items():
                if name in filtered_patterns:
                    continue
                for (j, k) in jks:
                    add_edge(j, k, name, self)
                    vertices_with_successors.add(j)
                    vertices_with_predecessors.add(k)
            to_keep = sorted(vertices_with_successors | vertices_with_predecessors | {0, n})

            # Remove isolated vertices
            for u in range(n):
                if u not in to_keep:
                    remove_vertex(u, self)

            # Add missing "any" edges
            for (i, u) in enumerate(to_keep):
                if u != 0 and u not in vertices_with_predecessors:
                    add_edge(to_keep[i - 1], u, "any", self)
                if u != n and u not in vertices_with_successors:
                    add_edge(u, to_keep[i + 1], "any", self)
        else:
            # The PatternAutomaton involves a single "any" arc
            to_remove = set()
            for u in vertices(self):
                if u not in {0, n}:
                    to_remove.add(u)
            for u in to_remove:
                remove_vertex(u, self)
            if len(word):
                add_edge(0, len(word), "any", self)

    def get_slice(self, e) -> tuple:
        """
        Retrieve the slice (pair of uint indices) related to an edge.
        Returns:
            The slice related to an arbitrary edge of this PatternAutomaton instance.
        """
        j = source(e, self)
        k = target(e, self)
        return (j, k)

    def get_infix(self, e: EdgeDescriptor) -> str:
        """
        Retrieve the infix (substring) related to an edge.
        Returns:
            The infix related to an arbitrary edge of this PatternAutomaton instance.
        """
        (j, k) = self.get_slice(e)
        return self.w[j:k]

    def __eq__(self, pa) -> bool:
        """
        Equality operators. This implementation relies on the important property
        that `PatternAutomaton` using `MultiGrepFonctorUltimate` or
        `MultiGrepFonctorLargest` are minimal.
        Args:
            pa: A `PatternAutomaton` instance.
        Returns:
            True iff `self` matches another `PatternAutomaton` instance.
        """
        if num_vertices(self) != num_vertices(pa) or num_edges(self) != num_edges(pa):
            # MultiGrepFonctorUltimate guarantees that two PatternAutomaton can
            # only be equal if they are of same size, because PatternAutomaton are
            # always minimal.
            return False
        return deterministic_inclusion(self, pa) == 0


def pattern_automaton_edge_weight(
    e: EdgeDescriptor,
    g: PatternAutomaton,
    map_name_density: dict = None
) -> float:
    a = label(e, g)
    return map_name_density.get(a, 1.0) if map_name_density else 1.0


def pattern_automaton_to_path(g: PatternAutomaton, **kwargs) -> list:
    s = initial(g)
    f = finals(g)
    assert len(f) == 1
    t = f.pop()

    pmap_vpreds = kwargs.pop("pmap_vpreds", None)
    if pmap_vpreds is None:
        map_vpreds = defaultdict(set)
        pmap_vpreds = make_assoc_property_map(map_vpreds)
    pmap_vdist = kwargs.pop("pmap_vdist", None)
    if pmap_vdist is None:
        map_vdist = defaultdict()
        pmap_vdist = make_assoc_property_map(map_vdist)
    pmap_eweight = kwargs.pop("pmap_eweight", None)
    map_name_density = kwargs.pop("map_name_density", None)
    assert pmap_eweight or map_name_density
    if pmap_eweight is None:
        pmap_eweight = make_func_property_map(
            partial(
                pattern_automaton_edge_weight,
                g=g,
                map_name_density=map_name_density
            )
        )

    dijkstra_shortest_path(
        g, s, t,
        pmap_eweight,
        pmap_vpreds,
        pmap_vdist,
        **kwargs
    )
    return make_path(g, s, t, pmap_vpreds)
