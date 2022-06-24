#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

"""Boost C++ functions wrapper."""

__author__ = "Marc-Olivier Buob, Maxime Raynal"
__maintainer__ = "Marc-Olivier Buob, Maxime Raynal"
__email__ = "marc-olivier.buob@nokia-bell-labs.com, maxime.raynal@nokia.com"
__copyright__ = "Copyright (C) 2022, Nokia"
__license__ = "BSD-3"

import multiprocessing, string, sys
from pprint import pformat
from pybgl.singleton import Singleton

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
from .regexp import MAP_NAME_RE, make_dfa_any, make_map_name_dfa

def make_name_density(map_name_dfa: dict, alphabet: str) -> dict:
    """
    Builds the dictionary mapping each pattern names with the corresponding language density.

    Args:
        map_name_dfa (dict): The pattern collection mapping each pattern name (``str``)
             with its corresponding ``Automaton`` instance.
        alphabet (set): A set gathering the characters of the alphabet.

    Returns:
        The corresponding mapping each pattern names (``str``) with the corresponding
        language density (``float``).
    """
    map_name_density = {
        name: language_density(dfa, alphabet)
        for (name, dfa) in map_name_dfa.items()
    }
    if "any" not in map_name_density.keys():
        map_name_density["any"] = language_density(
            make_dfa_any(alphabet),
            alphabet
        )
    return map_name_density


class PatternClusteringEnv(metaclass=Singleton):
    alphabet = set(string.printable)
    map_name_re = MAP_NAME_RE
    map_name_dfa = make_map_name_dfa(
        map_name_re,
        ["any", "float", "hexa", "int", "ipv4", "spaces", "uint", "word"]
    )
    map_name_density = make_name_density(map_name_dfa, alphabet)

    @classmethod
    def reset(cls):
        """
        Reset the ``PatternClusteringEnv`` singleton to its default settings.
        """
        cls.alphabet = set(string.printable)
        cls.set_patterns(
            MAP_NAME_RE,
            ["any", "float", "hexa", "int", "ipv4", "spaces", "uint", "word"]
        )

    @classmethod
    def set_patterns(cls, map_name_re: dict, names: iter =None):
        """
        Defines the patterns used in the pattern clustering.

        Args:
            map_name_re (dict): A dictionary mapping each pattern (``str``)
        """
        if "any" not in map_name_re:
            map_name_re["any"] = MAP_NAME_RE["any"]
        cls.map_name_re = map_name_re
        if not names:
            names = list(map_name_re.keys())
        cls.map_name_dfa = make_map_name_dfa(map_name_re, names)
        cls.map_name_density = make_name_density(cls.map_name_dfa, cls.alphabet)

    @classmethod
    def densities(cls) -> list:
        """
        Returns:
            The densities assigned to each pattern defined in ``self.map_name_dfa``.
        """
        return make_densities(cls.map_name_density)

    def __str__(self):
        return "\n".join([
            f"map_name_re = {pformat(self.map_name_re)}",
            f"map_name_density = {pformat(self.map_name_density)}",
            f"map_name_dfa = {pformat(self.map_name_dfa)}",
        ])

def make_pattern_automaton(w: str, map_name_dfa: dict, make_mg=None):
    """
    Builds a ``PatternAutomaton`` C++ instance from a input string.

    Args:
        w (str): The string to convert.
        map_name_dfa (dict): Maps each pattern name (``str``) with its corresponding
            ``Automaton``.
        make_mg (MultiGrepFunctor): The strategy used to build the PatternAutomaton.
            Defaults to ``None``.
    Returns:
        The ``PatternAutomaton`` C++ instance.
    """
    # Build the python PatternAutomaton
    g = PatternAutomaton(w, map_name_dfa, make_mg)

    # Transform python PatternAutomaton to a C++ PatternAutomaton
    map_name_id = {k: i for (i, k) in enumerate(sorted(map_name_dfa.keys()))}
    n = len(w) + 1
    _g = _PatternAutomaton(n, len(map_name_dfa), w)
    for e in edges(g):
        q = source(e, g)
        r = target(e, g)
        a = map_name_id[label(e, g)]
        _g.add_edge(q, r, a)
    return _g


def make_densities(map_name_density: dict = None) -> list:
    """
    Builds the language density vector.

    Args:
        map_name_density (dict): Maps mapping each pattern name (``str``)
            with the corresponding density (``float``).
    Returns:
        The corresponding densities, sorted by increasing pattern name.
    """
    if not map_name_density:
        map_name_density = PatternClusteringEnv.map_name_density
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
    Computes the pattern distance between two strings.

    Args:
        w1 (str): The first compared string.
        w2 (str): The second compared string.
        map_name_dfa (dict): Maps each pattern name (``str``) with its
            corresponding ``Automaton``.
        densities (list): A density vector. See ``make_densities()``.
        infinity (float): The infinite distance.
        normalized (bool): Pass ``True`` to get a distance between ``0.0`` and ``1.0``
            (resp. between ``0`` and ``len(w1) + len(w2)``)
            if it is normalized (resp. not normalized).
    Returns:
        The corresponding distance.
    """
    if not map_name_dfa:
        map_name_dfa = PatternClusteringEnv.map_name_dfa
    if not densities:
        densities = PatternClusteringEnv.densities()
    g1 = make_pattern_automaton(w1, map_name_dfa)
    g2 = make_pattern_automaton(w2, map_name_dfa)
    return (
        pattern_distance_normalized(g1, g2, densities, infinity) if normalized else
        _pattern_distance(g1, g2, densities, infinity)
    )


# pool.starmap prevents to use a lambda.
def make_pattern_automaton_python(w: str, map_name_dfa: dict, make_mg: MultiGrepFunctor = None):
    """
    ``PatternAutomaton.__init__`` wrapper.

    Args:
        w (str): The string to convert.
        map_name_dfa (dict): Maps each pattern name (``str``) with its
            corresponding ``Automaton``.
        make_mg (MultiGrepFunctor): The strategy used to build the PatternAutomaton.
            Defaults to ``None``.

    Returns:
        The corresponding ``PatternAutomaton`` python instance.
    """
    return PatternAutomaton(w, map_name_dfa, make_mg)


def make_pattern_automata(
    lines: list,
    map_name_dfa: dict,
    make_mg: callable = None
) -> list:
    """
    Converts input lines to the ``PatternAutomaton`` C++ instances.

    Args:
        lines (list): A list gathering the input lines (``str``).
        map_name_dfa (dict): Maps each pattern name (``str``) with its
            corresponding ``Automaton``.
        make_mg: A ``MultiGrepFunctor`` instance.
    Returns:
        The corresponding list of pattern automata.
    """

    # Transform python PatternAutomaton to a C++ PatternAutomaton
    def to_pc_boost_pattern_automaton(g: PatternAutomaton):
        map_name_id = {k: i for (i, k) in enumerate(sorted(map_name_dfa.keys()))}
        n = len(g.w) + 1
        _g = _PatternAutomaton(n, len(map_name_id), g.w)
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
    Computes the pattern clustering of input lines without aggregating duplicated PAs.

    Args:
        lines: A ``list(str)`` gathering the input lines.

        map_name_dfa: A ``dict{str : Automaton}`` mapping each pattern name
            with the corresponding Automaton.
        densities: A density vector. See ``make_densities()``.
        max_dist: The maximum distance between an element of a cluster and the
            cluster representative. As distances are normalized, this value should
            be between ``0.0`` and ``1.0``.
        use_async: Pass ``True`` to run computations using async calls. This accelerates
            computations.
        make_mg: A ``MultiGrepFunctor`` instance.
    Returns:
        A ``list(int)`` mapping each line index with its corresponding cluster identifier.
    """
    if not map_name_dfa:
        map_name_dfa = PatternClusteringEnv.map_name_dfa
    if not densities:
        densities = PatternClusteringEnv.densities()
    pattern_automata = make_pattern_automata(lines, map_name_dfa, make_mg)
    return _pattern_clustering(pattern_automata, densities, max_dist, use_async)


def group_by_identical_pa(pas: list, are_equal: callable = None) -> dict:
    """
    Groups matching ``PatternAutomaton`` python instances.

    Args:
        pas: A ``list(PatternAutomaton)`` instance.
        are_equal: A ``callable(PatternAutomaton, PatternAutomaton) -> bool``
            checking whether two PAs are homomorphic (pass ``None``
            if the compared PAs are minimal to accelerate the processing).
    Returns:
        A dictionary mapping each reference PAs to the matching instances found in ``pas``.
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
    Computes the pattern clustering of input lines by grouping matching PAs.

    This implies that lines having matching PatternAutomaton always fall in the same clusters
    which accelerate the code. Sometimes, this may lead to weird cluster, especially if some
    lines are unrelated and conform to the same ``PatternAutomaton``.

    Args:
        lines: A ``list(str)`` gathering the input lines.
        map_name_dfa: A ``dict{str : Automaton}`` mapping each pattern name
            with the corresponding Automaton.
        densities: A density vector. See ``make_densities()``.
        max_dist: The maximum distance between an element of a cluster and the
            cluster representative. As distances are normalized, this value should
            be between ``0.0`` and ``1.0``.
        use_async: Pass ``True`` to run computations using async calls. This accelerates
            computations.
        make_mg: A ``MultiGrepFunctor`` instance.
    Returns:
        A ``list(int)`` mapping each line index with its corresponding cluster identifier.
    """
    if not map_name_dfa:
        map_name_dfa = PatternClusteringEnv.map_name_dfa
    if not densities:
        densities = PatternClusteringEnv.densities()
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


pattern_clustering = pattern_clustering_without_preprocess
