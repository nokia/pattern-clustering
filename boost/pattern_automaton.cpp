#include "pattern_automaton.hpp"
#include <algorithm>  // std::fill
#include <sstream>    // std::ostringstream

PatternAutomaton::PatternAutomaton(
    std::size_t num_vertices,
    std::size_t alphabet_size,
    const std::string & word
):
    adjacencies(num_vertices),
    alphabet_size(alphabet_size),
    word(word)
{
    std::fill(
        this->adjacencies.begin(),
        this->adjacencies.end(),
        std::vector<State>(alphabet_size, BOTTOM)
    );
}

void PatternAutomaton::add_vertex() {
    this->adjacencies.push_back(
        std::vector<State>(this->num_vertices(), BOTTOM)
    );
}

void PatternAutomaton::add_edge(State q, State r, Label a) {
    std::size_t n = this->num_vertices();
    if (std::size_t(q) < n && std::size_t(r) < n && a < this->get_alphabet_size()) {
        this->adjacencies[q][a] = r;
    } else {
        std::ostringstream message;
        message << "add_edge(q = " << q << ", r = " << r << ", a = " + a << "):" << std::endl
            << "   0 <= q = " << q << " < r = " << r << " < this->num_vertices() = " << n << std::endl
            << "   a = " << a << " < alphabet_size = " << this->get_alphabet_size() << std::endl;
        throw std::runtime_error(message.str());
    }
}

PatternAutomaton::State PatternAutomaton::delta(State q, Label a) const {
    if (!(q < (int) this->num_vertices())) throw std::runtime_error("delta: !q < n");
    if (!(a < this->get_alphabet_size())) throw std::runtime_error("delta: !a < |Sigma|");
    return q == BOTTOM ? BOTTOM : this->adjacencies[q][a];
}

std::size_t PatternAutomaton::num_vertices() const {
    return this->adjacencies.size();
}

std::size_t PatternAutomaton::num_edges() const {
    std::size_t n = 0;
    for (std::size_t q = 0; q < this->num_vertices(); q++) {
        for (std::size_t a = 0; a < this->get_alphabet_size(); a++) {
            State r = this->delta(q, a);
            if (r != BOTTOM) {
                n++;
            }
        }
    }
    return n;
}

std::string PatternAutomaton::to_string() const {
    std::ostringstream oss;
    for (std::size_t q = 0; q < this->num_vertices(); q++) {
        for (std::size_t a = 0; a < this->get_alphabet_size(); a++) {
            State r = this->delta(q, a);
            if (r != BOTTOM) {
                oss << q << "--[" << a << "]-->" << r << std::endl;
            }
        }
    }
    return oss.str();
}

std::string PatternAutomaton::get_word() const {
    return this->word;
}

std::size_t PatternAutomaton::get_alphabet_size() const {
    return this->alphabet_size;
}

std::ostream & operator << (std::ostream & out, const PatternAutomaton & g) {
    out << g.to_string();
    return out;
}

