/*
This file is only required if you want to specify manually the Python bindings.
See https://www.boost.org/doc/libs/1_68_0/libs/python/doc/html/tutorial/tutorial/exposing.html
See in setup.py how to turn on bindings_auto.cpp generation.
*/

#include <boost/python.hpp>

namespace boost {
    namespace python {
        template <class F, class A1, class A2, class A3, class A4>
        void def(
            char const * name,
            F f,
            const A1 & a1,
            const A2 & a2,
            const A3 & a3,
            const A4 & a4
        ) {
            detail::def_from_helper(
                name, f,
                detail::def_helper<A1, A2, A3, A4>(a1, a2, a3, a4)
            );
        }
    }
}

#include "bindings_stl.hpp"
#include "density.hpp"
#include "lcs_distance.hpp"
#include "pattern_automaton.hpp"
#include "pattern_clustering.hpp"
#include "pattern_distance.hpp"

// {python <-> STL objects} converters
// Custom converter, allowing to manipulate dict and list python-side
static list_to_vector<std::vector<PatternAutomaton> > reg1;
static list_to_vector<std::vector<Density> > reg2;
static vector_to_list<Clusters> reg3;

BOOST_PYTHON_MODULE(pattern_clustering) // Pass the python module name (as defined in setup.py)
{
    using namespace boost::python;

    // pattern_automaton.hpp
    class_<PatternAutomaton>(
        "PatternAutomaton",
        init<optional<
            std::size_t,
            std::size_t,
            const std::string &
        > > ((
            arg("num_vertices") = 0,
            arg("alphabet_size") = 0,
            arg("word") = ""
        ))
    )
        .def("add_vertex",      &PatternAutomaton::add_vertex)
        .def("add_edge",        &PatternAutomaton::add_edge)
        .def("delta",           &PatternAutomaton::delta)
        .def("num_vertices",    &PatternAutomaton::num_vertices)
        .def("num_edges",       &PatternAutomaton::num_edges)
        .def("__str__",         &PatternAutomaton::to_string)
        .def("alphabet_size",   &PatternAutomaton::get_alphabet_size)
        .def("get_word",        &PatternAutomaton::get_word)
    ;

    // lcs_distance.hpp
    def("lcs_distance", &::lcs_distance);

    // pattern_distance.hpp
    def(
        "pattern_distance",
        &::pattern_distance,
        arg("pa1"),
        arg("pa2"),
        arg("densities"),
        arg("max_dist") = std::numeric_limits<double>::max()
    );
    def(
        "pattern_distance_normalized",
        &::pattern_distance_normalized,
        arg("pa1"),
        arg("pa2"),
        arg("densities"),
        arg("max_dist") = std::numeric_limits<double>::max()
    );

    // pattern_clustering.hpp
    def(
        "pattern_clustering",
        &::pattern_clustering,
        arg("pattern_automata"),
        arg("densities"),
        arg("max_dist") = 0.5,
        arg("use_async") = true
    );

}
