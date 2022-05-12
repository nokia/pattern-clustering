#ifndef STL_UTIL_HPP
#define STL_UTIL_HPP

#include <list>
#include <map>
#include <ostream>
#include <queue>
#include <set>
#include <vector>

template <typename T>
std::ostream & operator << (std::ostream & out, const std::vector<T> & v) {
    out << '[';
    for (auto x : v) out << ' ' << x;
    out << " ]";
    return out;
}

template <typename T>
std::ostream & operator << (std::ostream & out, const std::list<T> & l) {
    out << '[';
    for (auto x : l) out << ' ' << x;
    out << " ]";
    return out;
}

template <typename T>
std::ostream & operator << (std::ostream & out, const std::set<T> & s) {
    out << '{';
    for (auto x : s) out << ' ' << x;
    out << " }";
    return out;
}

template <typename T1, typename T2>
std::ostream & operator << (std::ostream & out, const std::pair<T1, T2> & p) {
    out << '(' << p.first << ", " << p.second << ')';
    return out;
}

template <typename K, typename V>
std::ostream & operator << (std::ostream & out, const std::map<K, V> & m) {
    out << '{';
    for (auto p : m) out << ' ' << p;
    out << " }";
    return out;
}

template <typename T, typename Container, typename Compare>
std::ostream & operator << (
    std::ostream & out,
    std::priority_queue<T, Container, Compare> q
) {
    // We pass a copy of q
    out << '[';
    while (!q.empty()) {
        out << ' ' << q.top();
        q.pop();
    }
    out << " ]";
    return out;
}


#endif
