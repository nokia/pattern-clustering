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

from collections import defaultdict
from itertools import combinations
from pybgl.automaton import BOTTOM, initial, is_final, delta
from pybgl.deterministic_inclusion import deterministic_inclusion


def multi_grep(
    w: str,
    map_name_dfa: dict,
    callback: callable = lambda name, j, k, w: None,
):
    """
    Search sub-strings of a string matched by multiple patterns.
    Args:
        w: A ̀`str` containing the word to process.
        map_name_dfa: A `dict{Name : Automaton}` mapping each pattern
            name with its corresponding DFA.
        callback: A `callable(Name, int, int, str)` called whenever
            `w[j:k]` is matched by pattern `name`.
    """

    def make_map_name_q_js_next():
        return {
            name: defaultdict(set)
            for (name, g) in map_name_dfa.items()
        }

    m = len(w)
    map_name_q_js = {
        name: {initial(g): {0}}
        for (name, g) in map_name_dfa.items()
    }

    map_name_q_js_next = make_map_name_q_js_next()
    for k in range(m):
        a = w[k]
        for (name, g) in map_name_dfa.items():
            map_q_js = map_name_q_js[name]
            for (q, js) in map_q_js.items():
                if not js:
                    continue
                r = delta(q, a, g)
                if r is BOTTOM:
                    map_name_q_js_next[name][q] = set()
                else:
                    map_name_q_js_next[name][r] |= map_q_js[q]
                    if is_final(r, g):
                        for j in js:
                            callback(name, j, k + 1, w)
            map_name_q_js_next[name][initial(g)] |= {k + 1}
        map_name_q_js = map_name_q_js_next
        map_name_q_js_next = make_map_name_q_js_next()


def multi_grep_with_delimiters(
    word: str,
    map_name_dfa: dict,
    callback: callable = lambda i, j, k, w: None,
    is_pattern_separator: callable = lambda name: False,
    is_pattern_left_separated: callable = lambda name: True,
    is_pattern_right_separated: callable = lambda name: True
):
    """
    Search sub-strings of a string matched by multiple patterns, possibly
    delimited by a predefined collection of separator patterns.
    Args:
        word: A ̀`str` containing the word to process.
        map_name_dfa: A `dict{Name : Automaton}` mapping each pattern name with its corresponding DFA.
        callback: A `callable(Name, int, int, str)` called whenever `w[j:k]` is matched by pattern `name`.
        is_pattern_separator: A ̀`callable(Name) -> bool` return True if the pattern `name` is a separator.
        is_pattern_left_separated: A ̀`callable(Name) -> bool` return True if the pattern `name` must be preceded by a
            separator pattern or located at the beginning of `w`.
        is_pattern_right_separated: A ̀`callable(Name) -> bool` return True if the pattern `name` must be followed by a
            separator pattern or located at the end of `w`.
    """
    # multi_grep on separating patterns
    map_name_dfa_separator = {
        name: dfa
        for (name, dfa) in map_name_dfa.items()
        if is_pattern_separator(name)
    }
    functor_delimiters = MultiGrepFunctorLargest()
    multi_grep(word, map_name_dfa_separator, functor_delimiters)

    js = {0} | {
        k
        for (i, jks) in functor_delimiters.indices().items()
        for (j, k) in jks
    }

    ks = {len(word)} | {
        j
        for (i, jks) in functor_delimiters.indices().items()
        for (j, k) in jks
    }

    # multi_grep on other patterns
    def filtered_callback(name, j, k, w):
        if is_pattern_separator(name):
            return
        elif j not in js and is_pattern_left_separated(name):
            return
        elif k not in ks and is_pattern_right_separated(name):
            return
        else:
            callback(name, j, k, w)

    multi_grep(
        word,
        map_name_dfa,
        callback=lambda name, j, k, w: filtered_callback(name, j, k, w)
    )


class MultiGrepFunctor:
    def __call__(self, i, j, k, w):
        """
        Functor method.
        Args:
            i: `int` corresponding to a DFA identifier.
            j: `int` corresponding to the beginning of a substring caught by Automaton `i`.
            k: `int` corresponding to the end of a substring caught by Automaton `i`.
            w: The input `str`.
        """
        raise NotImplementedError

    def indices(self) -> dict:
        """
        Returns: A dict{i : [(j, k)]} where
            `i` is an `int` corresponding to a DFA identifier.
            `j` is an `int` corresponding to the beginning of a substring caught by Automaton `i`.
            `k` is an `int` corresponding to the end of a substring caught by Automaton `i`.
        """
        raise NotImplementedError


class MultiGrepFunctorAll(MultiGrepFunctor):
    """
    `MultiGrepFunctorAll` catches (for each pattern Pi and for each index `j`) each substring `w[j:k]` matching Pi.
    """

    def __init__(self):
        self.map_i_jk = defaultdict(list)

    def __call__(self, i, j, k, w):
        self.map_i_jk[i].append((j, k))

    def indices(self) -> dict:
        return self.map_i_jk


class MultiGrepFunctorLargest(MultiGrepFunctor):
    """
    `MultiGrepFunctorLargest` catches (for each pattern Pi and for each index j)
    the largest w[j:k] matching Pi.
    """

    def __init__(self):
        self.map_i_j_k = defaultdict(lambda: defaultdict(lambda: None))

    def __call__(self, i, j, k, w):
        # As we read w from left to right, k > self.map_pattern_indices[i][j]
        self.map_i_j_k[i][j] = k

    def indices(self) -> dict:
        # Rebuild {i : [(j, k)]} for each (i, j) pair
        result = defaultdict(list)
        for i in self.map_i_j_k:
            for k in set(self.map_i_j_k[i].values()):
                result[i] += [(
                    min(
                        j for j in self.map_i_j_k[i].keys()
                        if self.map_i_j_k[i][j] == k
                    ),
                    k
                )]
            result[i] = sorted(result[i])
        return result


class MultiGrepFunctorGreedy(MultiGrepFunctorLargest):
    """
    `MultiGrepFunctorGreedy` catches (for each pattern Pi and for each index j)
    the largest  w[j′:k] matching Pi and s.t.  j′ < j.
    """

    def __init__(self):
        super().__init__()
        self.map_i_k_j = defaultdict(lambda: defaultdict(lambda: None))

    def __call__(self, i, j, k, w):
        j_ = self.map_i_k_j[i][k]
        if j_ is None or j < j_:
            self.map_i_k_j[i][k] = j
            super().__call__(i, j, k, w)


def make_patterns_inclusions(map_name_dfa: dict) -> set:
    pattern_inclusions = set()
    for (i, (name_i, gi)) in enumerate(map_name_dfa.items()):
        for (j, (name_j, gj)) in enumerate(map_name_dfa.items()):
            if j <= i:
                continue
            inc_ij = deterministic_inclusion(gi, gj)
            if inc_ij == -1:
                pattern_inclusions.add((name_j, name_i))
            elif inc_ij == 1:
                pattern_inclusions.add((name_i, name_j))
    return pattern_inclusions


def multi_grep_fonctor_to_dict(w: str, fonctor: MultiGrepFunctor) -> dict:
    """
    Convert a `MultiGrepFunctor` to a `dict`.
    Args:
        w: The input `str`.
        fonctor: A `MultiGrepFunctor` instance (after populating it with `multi_grep`).
    Returns:
        The `dict{str : list(str)} mapping each pattern names with the list of matching
        substrings of `w` (according to `fonctor`).
    """
    return {
        name: [w[j:k] for (j, k) in slices]
        for (name, slices) in fonctor.indices().items()
    }


def multi_grep_fonctor_to_string(w: str, fonctor: MultiGrepFunctor) -> str:
    """
    Convert a `MultiGrepFunctor` to a `str`.
    Args:
        w: The input `str`.
        fonctor: A `MultiGrepFunctor` instance (after populating it with `multi_grep`).
    Returns:
        The `str` representation of `fonctor`.
    """
    return "\n".join([
        "%-5s: %s" % (k, v)
        for (k, v) in multi_grep_fonctor_to_dict(w, fonctor).items()
    ])


def print_multi_grep_fonctor(w: str, fonctor: MultiGrepFunctor):
    """
    Print a `MultiGrepFunctor` to a `str`.
    Args:
        w: The input `str`.
        fonctor: A `MultiGrepFunctor` instance (after populating it with `multi_grep`).
    """
    print(multi_grep_fonctor_to_string(w, fonctor))
