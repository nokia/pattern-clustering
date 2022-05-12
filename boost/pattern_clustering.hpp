#ifndef PATTERN_CLUSTERING_HPP
#define PATTERN_CLUSTERING_HPP

#include <vector>
#include "density.hpp"
#include "pattern_automaton.hpp"

typedef std::vector<std::size_t> Clusters;
typedef std::vector<PatternAutomaton> PatternAutomata;
typedef std::vector<double> Densities;

Clusters pattern_clustering(
    const PatternAutomata & pattern_automata,
    const Densities & densities,
    double max_dist = 0.5,
    bool use_async = true
);

#endif

