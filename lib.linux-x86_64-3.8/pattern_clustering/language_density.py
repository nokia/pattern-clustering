#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

"""Language density module"""

__author__     = "Maxime Raynal, Marc-Olivier Buob"
__maintainer__ = "Maxime Raynal, Marc-Olivier Buob"
__email__      = "maxime.raynal@nokia.com, marc-olivier.buob@nokia-bell-labs.com"
__copyright__  = "Copyright (C) 2022, Nokia"
__license__    = "BSD-3"

import string
from collections        import defaultdict
from pybgl.automaton    import Automaton, BOTTOM, finals, initial, is_final

def language_density(
    g        :Automaton,
    alphabet :set = None,
    n_max    :int = 30,
    series   :callable = None
) -> float:
    """
    Computes the language density of an ``Automaton`` for a given alphabet.

    Args:
        g (Automaton): The Automaton representing the language.
        alphabet (set): A set gathering the characters of the alphabet.
            You could pass ``list(pybgl.automaton.alphabet(g))``
            which computes the smallest valid alphabet in O(num_edges(g)).
        n_max (int): An unsigned ``int`` corresponding to the highest monom degree used
            to compute the language density.
            The greater ``n_max``, the better the accuracy, but the slower the computation.
        series (callable): ``Callback(int) -> float`` returning the coefficient
            of a monome according to its degree.
    Returns:
        A ``float`` in [0.0, 1.0] corresponding to the language density of ``g``
        according to ``alphabet``.
    """
    if not alphabet:
        alphabet = set(string.printable)
    if series is None:
        def series(k):
            return 1 / (2 ** k)
    m = defaultdict(int)
    q0 = initial(g)
    m[q0] = series(0)
    result = m[q0] if is_final(q0, g) else 0
    for n in range(1, n_max):
        m2 = defaultdict(int)
        for (q, map_a_r) in g.m_adjacencies.items():
            for (a, r) in map_a_r.items():
                if r is not BOTTOM:
                    if r in finals(g):
                        result += series(n) * m[q] / (len(alphabet) ** n)
                    m2[r] += m[q]
        m = m2
    return result
