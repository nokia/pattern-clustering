#include "pattern_distance.hpp"

#include <limits>                           // std::numeric_limits
#include <queue>                            // std::priority_queue
#include <string>                           // std::string
#include <tuple>                            // std::tuple
#include <boost/numeric/ublas/matrix.hpp>   // boost::numeric::ublas::matrix
#include "lcs_distance.hpp"

#include "stl_util.hpp"

// It's important to put the cumulated distance first, so that heap_item_t are
// naturally correctly ordered in heap_t.
typedef std::tuple<
    double,      // d: cumulated distance
    std::size_t, // i1: current position in w1
    std::size_t  // i2: current position in w2
> heap_item_t;

// For debug, so that after include "stl_utils.hpp", you may use: std::cout << heap << std::endl;
std::ostream & operator << (std::ostream & out, const heap_item_t & h) {
    out << "<i1="  << std::get<0>(h)
        << ", i2=" << std::get<1>(h)
        << ", d="  << std::get<2>(h)
        << ">";
    return out;
}

typedef std::priority_queue<
    heap_item_t,
    std::vector<heap_item_t>,
    std::greater<heap_item_t>
> heap_t; // heap_min

double pattern_distance(
    const PatternAutomaton & g1,
    const PatternAutomaton & g2,
    const std::vector<Density> & densities,
    double max_dist
) {
    // We assume that vertex identifiers of g1 (resp. g2) conforms to w1 (resp. w2) indices.
    // This means that vertex i1 (resp. i2)  means that we have reached w1[i1] (resp. w2[i2]).
    const std::string &
        w1 = g1.get_word(),
        w2 = g2.get_word();
    std::size_t
        w1_len = w1.size(),
        w2_len = w2.size();
    unsigned k_max = densities.size();

    boost::numeric::ublas::matrix<bool> visited(w1_len + 1, w2_len + 1, false);
    heap_t heap;
    heap.push(std::make_tuple(0, 0, 0.0));

    // Lambda function: pushes the new item to the heap
    auto heap_push = [&heap] (
        PatternAutomaton::State i1_next,
        PatternAutomaton::State i2_next,
        double current_dist,
        double edge_weight
    ) -> void {
        heap_item_t heap_item = std::make_tuple(
            current_dist + edge_weight,
            i1_next, i2_next
        );
        heap.push(heap_item);
    };

    // Lambda function: returns the reached state (in the edit graph sense).
    auto edit_graph_delta = [] (
        std::size_t i,
        std::size_t k,
        const PatternAutomaton & g
    ) -> std::size_t {
        PatternAutomaton::State j = g.delta(i, k);
        return j == BOTTOM ? i : std::size_t(j);
    };

    while (!heap.empty()) {
        double current_dist;
        std::size_t i1, i2;
        std::tie(current_dist, i1, i2) = heap.top();
        heap.pop();
        if (current_dist >= max_dist) {
            return -1;
        } else if (i1 == w1_len && i2 == w2_len) {
            return current_dist;
        } else if (visited(i1, i2)) {
            continue;
        }
        visited(i1, i2) = true;
        for (std::size_t k = 0; k < k_max; k++) {
            std::size_t
                j1 = edit_graph_delta(i1, k, g1),
                j2 = edit_graph_delta(i2, k, g2),
                n1 = j1 - i1,
                n2 = j2 - i2;

            if (j1 != i1 && j2 != i2) {
                // Diagonal edge
                std::string
                    s1 = w1.substr(i1, n1),
                    s2 = w2.substr(i2, n2);
                double
                    lcs_weight = (s1 == s2 ? 0.0 : n1 + n2 - 2 * lcs_length(s1, s2)),
                    edge_weight = lcs_weight * densities[k];
                heap_push(j1, j2, current_dist, edge_weight);
            }
            if (j1 != i1) {
                // Horizontal edge
                heap_push(j1, i2, current_dist, n1);
            }
            if (j2 != i2) {
                // Vertical edge
                heap_push(i1, j2, current_dist, n2);
            }
        }
    }
    return -2;
}

double pattern_distance_normalized(
    const PatternAutomaton & g1,
    const PatternAutomaton & g2,
    const std::vector<Density> & densities,
    double max_dist = std::numeric_limits<double>::max()
) {
    size_t norm = g1.get_word().size() + g2.get_word().size();
    double d = pattern_distance(g1, g2, densities, max_dist * norm);
    return d <= 0 ? d : d / norm;
}
