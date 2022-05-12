#include "pattern_clustering.hpp"

#include <algorithm>
#include <future>
#include <iostream>
#include <limits>
#include <thread>
#include <vector>
#include "pattern_distance.hpp"
#include "stl_util.hpp"

#define NONE std::numeric_limits<std::size_t>::max()
#define INVALID_DISTANCE std::numeric_limits<double>::max()

template <typename T>
inline bool is_ready(const std::future<T> & future) {
    return future.valid() && future.wait_for(std::chrono::seconds(0)) == std::future_status::ready;
}

static std::pair<std::size_t, double> find_closest_neighbor(
    const PatternAutomata & pas,
    const std::vector<std::size_t> & js,
    std::size_t i,
    const Densities & densities,
    double max_dist,
    bool use_async = true
) {
    if (js.empty()) {
        return std::make_pair(NONE, 0);
    }
    const PatternAutomaton & pa = pas[i];
    double dist = max_dist;
    std::size_t j = NONE;

    // Async way
    if (use_async) {
        // 1) Queue jobs
        std::vector<std::future<double>> futures;
        std::size_t num_futures = js.size();
        for (std::size_t k = 0; k < num_futures; k++) {
            std::size_t j = js[k];
            const PatternAutomaton & pa_repr = pas[j];
            futures.push_back(
                std::async(
                    std::launch::async,
                    [&]() {
                        return pattern_distance_normalized(pa_repr, pa, densities, max_dist);
                    }
                )
            );
        }

        // 2) Wait until jobs are ready
        std::size_t num_futures_ready = 0;
        do {
            for (std::size_t k = 0; k < num_futures; k++) {
                auto & future = futures[k];
                if (is_ready(future)) {
                    double d = future.get();
                    if (d >= 0 && d < dist) {
                        dist = d;
                        j = js[k];
                    }
                    num_futures_ready++;
                }
            }
        } while (num_futures_ready < num_futures);
    } else {
        // Mono thread way
        for (std::size_t k = 0; k < js.size(); k++) {
            std::size_t j_cur = js[k];
            const PatternAutomaton pa_repr = pas[j_cur];
            double d = pattern_distance_normalized(pa_repr, pa, densities, dist);
            if (d >= 0 && d < dist) {
                dist = d;
                j = j_cur;
            }
        }
    }

    return std::make_pair(j, dist);
}

Clusters pattern_clustering(
    const PatternAutomata & pas,
    const Densities & densities,
    double max_dist,
    bool use_async
) {
    std::size_t n = pas.size();
    Clusters clusters(n, NONE);
    std::vector<std::size_t> pas_repr;
    for (std::size_t i = 0; i < n; i++) {
        std::size_t j;
        double dist;
        std::tie(j, dist) = find_closest_neighbor(pas, pas_repr, i, densities, max_dist, use_async);
        if (j == NONE || dist > max_dist) {
            pas_repr.push_back(i);
            clusters[i] = i;
        } else {
            clusters[i] = j;
        }
    }
    return clusters;
}

