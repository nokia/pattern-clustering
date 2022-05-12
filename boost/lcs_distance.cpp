#include "lcs_distance.hpp"
#include <boost/numeric/ublas/matrix.hpp>   // boost::numeric::ublas::matrix

#include <iostream>

std::size_t lcs_length(
    const std::string & w1,
    const std::string & w2
) {
    if (w1 == w2) return w1.size();
    std::size_t
        n1 = w1.size(),
        n2 = w2.size();
    boost::numeric::ublas::matrix<std::size_t> score(n1 + 1, n2 + 1);
    for (std::size_t i1 = 0; i1 <= n1; i1++) {
        for (std::size_t i2 = 0; i2 <= n2; i2++) {
            score(i1, i2) = std::max({
                i1 > 0 ? score(i1 - 1, i2) : 0,
                i2 > 0 ? score(i1, i2 - 1) : 0,
                i1 > 0 && i2 > 0 ? score(i1 - 1, i2 - 1) + (w1[i1 - 1] == w2[i2 - 1]) : 0
            });
        }
    }
    return score(n1, n2);
}

std::size_t lcs_distance(
    const std::string & w1,
    const std::string & w2
) {
    return w1.size() + w2.size() - 2 * lcs_length(w1, w2);
}
