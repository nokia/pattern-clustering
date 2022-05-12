#ifndef PATTERN_DISTANCE_HPP
#define PATTERN_DISTANCE_HPP

#include <vector>
#include "density.hpp"
#include "pattern_automaton.hpp"

double pattern_distance(
    const PatternAutomaton & pa1,
    const PatternAutomaton & pa2,
    const std::vector<Density> & densities,
    double max_dist // Not normalized
);

double pattern_distance_normalized(
    const PatternAutomaton & pa1,
    const PatternAutomaton & pa2,
    const std::vector<Density> & densities,
    double max_dist // Normalized, between 0.0 and 1.0
);

#endif
