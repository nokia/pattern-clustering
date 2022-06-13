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

import multiprocessing, string, sys

try:
    # Import from C++
    # Naming convention: symbols from pc_boost are prefixed by _ to prevent
    # them to clash with those from the python module.
    from pattern_clustering.pattern_clustering import PatternAutomaton as _PatternAutomaton
    from pattern_clustering.pattern_clustering import pattern_distance as _pattern_distance
    from pattern_clustering.pattern_clustering import pattern_clustering as _pattern_clustering
    from pattern_clustering.pattern_clustering import pattern_distance_normalized
except ImportError:
    print("pattern_clustering is not yet installed and so the C++ objects cannot be imported!", file=sys.stderr)
    import sys
    print(sys.path)
    sys.exit()

from .language_density import language_density
from .pattern_automaton import *
from .regexp import make_dfa_any, make_map_name_dfa

class PatternClusteringEnv:
    def __init__(self, names: list = None, alphabet: set = None):
        """
        Creates the parameters required to run pattern distance
        and pattern clustering computations.
            map_name_density: A `dict{str : double}` mapping each pattern name
                with the corresponding density.
            map_name_dfa: A `dict{str : Automaton}` mapping each pattern name
                with the corresponding Automaton.
        Args:
            names: A `list(str)` such that each string corresponds to
                a pattern name defined in `pattern_clustering.pattern`.
            alphabet: The set of characters supported by the crafted
                Automaton instances.
        """
        if not alphabet:
            alphabet = set(string.printable)
        self.alphabet = alphabet

        # `names` refers to types matched by MultiGrep to build pattern automata.
        # Thus, you should not include "any" to improve performance.
        if not names:
            names = ["float", "hexa", "int", "ipv4", "spaces", "uint", "word"]
        self.map_name_dfa = make_map_name_dfa(names)

        # Note that the density of "any" is required in the latter.
        self.map_name_density = {
            name: language_density(dfa, alphabet)
            for (name, dfa) in self.map_name_dfa.items()
        }
        if "any" not in self.map_name_density.keys():
            self.map_name_density["any"] = language_density(make_dfa_any(alphabet), alphabet)

    @property
    def densities(self):
        return make_densities(self.map_name_density)


def make_pattern_automaton(w, map_name_dfa, make_mg=None):
    """
    Build a `PatternAutomaton` C++ instance.
    Args:
        w: A `str` storing the string.
        map_name_dfa: A `dict{str : Automaton}` mapping each pattern name
            with the corresponding Automaton.
        make_mg: A `MultiGrepFonctor` instance.
    Returns:
        The `PatternAutomaton` C++ instance.
    """
    # Transform python PatternAutomaton to a C++ PatternAutomaton
    g = PatternAutomaton(w, map_name_dfa, make_mg)
    if "any" not in map_name_dfa.keys():
        # If some string is not caught by any pattern, it results to an "any" arc in
        # in the PatternAutomaton, and the "any" pattern might not be declared in
        # map_name_dfa.
        map_name_dfa["any"] = make_dfa_any()
    map_name_id = {k: i for (i, k) in enumerate(sorted(map_name_dfa.keys()))}
    n = len(w) + 1
    _g = _PatternAutomaton(n, len(map_name_dfa), w)
    for e in edges(g):
        q = source(e, g)
        r = target(e, g)
        a = map_name_id[label(e, g)]
        _g.add_edge(q, r, a)
    return _g


# Default parameters
PATTERN_CLUSTERING_ENV = PatternClusteringEnv(names=None, alphabet=None)

def make_densities(map_name_density: dict = None) -> list:
    """
    Build the language density vector.
    Args:
        map_name_density: A `dict{str : double}` mapping each pattern name
            with the corresponding density.
    Returns:
        The corresponding densities, sorted by increasing pattern name.
    """
    if not map_name_density:
        map_name_density = PATTERN_CLUSTERING_ENV.map_name_density
    return [map_name_density[name] for name in sorted(map_name_density.keys())]


# Default parameters
INFINITY = 100000


def pattern_distance(
    w1: str,
    w2: str,
    map_name_dfa: dict = None,
    densities: list = None,
    infinity: float = INFINITY,
    normalized: bool = False
) -> float:
    """
    Compute the pattern distance between two strings.
    Args:
        w1: An `str` instance.
        w2: An `str` instance.
        map_name_dfa: A `dict{str : Automaton}` mapping each pattern name
            with the corresponding Automaton.
        densities: A density vector. See `make_densities()`.
        infinity: The infinite distance.
        normalized: Pass `True` to get a distance in [0, 1],
            otherwise in [0, len(w1) + len(w2)]
    Returns:
        The corresponding distance.
    """
    if not map_name_dfa:
        map_name_dfa = PATTERN_CLUSTERING_ENV.map_name_dfa
    if not densities:
        densities = PATTERN_CLUSTERING_ENV.densities
    g1 = make_pattern_automaton(w1, map_name_dfa)
    g2 = make_pattern_automaton(w2, map_name_dfa)
    return (
        pattern_distance_normalized(g1, g2, densities, infinity) if normalized else
        _pattern_distance(g1, g2, densities, infinity)
    )


# pool.starmap prevents to use a lambda.
def make_pattern_automaton_python(w, map_name_dfa, make_mg=None):
    """
    `PatternAutomaton.__init__` wrapper.
    """
    return PatternAutomaton(w, map_name_dfa, make_mg)


def make_pattern_automata(
    lines: list,
    map_name_dfa: dict,
    make_mg: callable = None
) -> list:
    """
    Converts input lines to the `PatternAutomaton` C++ instances.
    Args:
        lines: A `list(str)` gathering the input lines.
        map_name_dfa: A `dict{str : Automaton}` mapping each pattern name
            with the corresponding Automaton.
        make_mg: A `MultiGrepFonctor` instance.
    Returns:
        The corresponding list of pattern automata.
    """

    # Transform python PatternAutomaton to a C++ PatternAutomaton
    def to_pc_boost_pattern_automaton(g: PatternAutomaton):
        map_name_id = {k: i for (i, k) in enumerate(sorted(map_name_dfa.keys()))}
        n = len(g.w) + 1
        _g = _PatternAutomaton(n, len(map_name_dfa), g.w)
        for e in edges(g):
            q = source(e, g)
            r = target(e, g)
            a = map_name_id[label(e, g)]
            _g.add_edge(q, r, a)
        return _g

    # Parallelize PatternAutomata construction
    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        pas = pool.starmap(
            make_pattern_automaton_python,
            [(line, map_name_dfa, make_mg) for line in lines]
        )
    return [
        to_pc_boost_pattern_automaton(pa)
        for pa in pas
    ]


def pattern_clustering_without_preprocess(
    lines: list,
    map_name_dfa: dict = None,
    densities: list = None,
    max_dist: float = 0.6,
    use_async: bool = True,
    make_mg: callable = None
) -> list:
    """
    Compute the pattern clustering of input lines.
    You should rather use `pattern_clustering_with_preprocess` aka `pattern_clustering`
    to accelerate computations.
    Args:
        lines: A `list(str)` gathering the input lines.
        map_name_dfa: A `dict{str : Automaton}` mapping each pattern name
            with the corresponding Automaton.
        densities: A density vector. See `make_densities()`.
        max_dist: The maximum distance between an element of a cluster and the
            cluster representative. As distances are normalized, this value should
            be lower than 1.0.
        use_async: Pass `True` to run computations using async calls. This accelerates
            computations.
        make_mg: A `MultiGrepFonctor` instance.
    Returns:
        A `list(int)` mapping each line index with its corresponding cluster identifier.
    """
    if not map_name_dfa:
        map_name_dfa = PATTERN_CLUSTERING_ENV.map_name_dfa
    if not densities:
        densities = PATTERN_CLUSTERING_ENV.densities
    pattern_automata = make_pattern_automata(lines, map_name_dfa, make_mg)
    return _pattern_clustering(pattern_automata, densities, max_dist, use_async)


def group_by_identical_pa(pas: list, are_equal: callable = None) -> dict:
    """
    Group matching `PatternAutomaton` python instances.
    Args:
        pas: A `list(PatternAutomaton)` instance.
        are_equal: A `callable(PatternAutomaton, PatternAutomaton) -> bool`
            checking whether two PAs are homomorphic. If the compared PAs
            are minimal you may pass `None`.
    Returns:
        A `dict{int : list(int)}` grouping similar PA in the same key.
        Keys and values correspond to indices of `pas`.
        The key always appears in the mapped values.
    """
    if are_equal is None:
        def are_equal(pa1, pa2):
            return pa1 == pa2

    ref_pa_indices = list()
    map_refpa_pas = dict()
    for (i, pa) in enumerate(pas):
        ref_pai = next(
            (
                ref_pai
                for ref_pai in ref_pa_indices
                if are_equal(pas[ref_pai], pa)
            ),
            None
        )
        if ref_pai is not None:
            map_refpa_pas[ref_pai].append(i)
        else:
            ref_pa_indices.append(i)
            map_refpa_pas[i] = [i]
    return map_refpa_pas


def pattern_clustering_with_preprocess(
    lines: list,
    map_name_dfa: dict = None,
    densities: list = None,
    max_dist: float = 0.6,
    use_async: bool = True,
    make_mg: callable = None
) -> list:
    """
    Compute the pattern clustering of input lines.
    If some lines lead to the same PatternAutomata, computations are optimized to prevent
    duplicated computations.
    Args:
        lines: A `list(str)` gathering the input lines.
        map_name_dfa: A `dict{str : Automaton}` mapping each pattern name
            with the corresponding Automaton.
        densities: A density vector. See `make_densities()`.
        max_dist: The maximum distance between an element of a cluster and the
            cluster representative. As distances are normalized, this value should
            be lower than 1.0.
        use_async: Pass `True` to run computations using async calls. This accelerates
            computations.
        make_mg: A `MultiGrepFonctor` instance.
    Returns:
        A `list(int)` mapping each line index with its corresponding cluster identifier.
    """
    if not map_name_dfa:
        map_name_dfa = PATTERN_CLUSTERING_ENV.map_name_dfa
    if not densities:
        densities = PATTERN_CLUSTERING_ENV.densities
    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        pas = pool.starmap(
            make_pattern_automaton_python,
            [(line, map_name_dfa) for line in lines]
        )

    # Group pattern automat by distinct PA. As PAs are indexed by rows,
    # this indexes rows by reference row.
    map_refrow_rows = group_by_identical_pa(pas)
    ref_rows = [ref_row for ref_row in map_refrow_rows.keys()]

    # Run the pattern clustering only for the reference lines.
    distinct_lines = [lines[row] for row in ref_rows]
    ref_clusters = _pattern_clustering(
        make_pattern_automata(distinct_lines, map_name_dfa, make_mg),
        densities,
        max_dist,
        use_async
    )

    # Map each row with its corresponding cluster
    clusters = [None] * len(lines)
    for (ref_row, cluster) in zip(ref_rows, ref_clusters):
        clusters[ref_row] = cluster
        for row in map_refrow_rows[ref_row]:
            clusters[row] = cluster
    return clusters


pattern_clustering = pattern_clustering_with_preprocess
