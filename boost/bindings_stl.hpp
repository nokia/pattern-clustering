#ifndef BINDINGS_STL_HPP

#include <map>
#include <boost/python/dict.hpp>     // dict
#include <boost/python/list.hpp>     // list
#include <boost/python/refcount.hpp> // incref

namespace bpy = boost::python;

// https://stackoverflow.com/questions/6116345/boostpython-possible-to-automatically-convert-from-dict-stdmap

template <typename Map>
struct map_to_dict {
    map_to_dict() {
        bpy::to_python_converter<Map, map_to_dict<Map> >();
    }

    static PyObject * convert(const Map & map) {
        //bpy::dict dictionary(map); // This segfaults :(
        bpy::dict dictionary;
        for (auto p : map) {
            dictionary[p.first] = p.second;
        }
        return bpy::incref(dictionary.ptr());
    }
};

template <typename Vector>
struct vector_to_list {
    vector_to_list() {
        bpy::to_python_converter<Vector, vector_to_list<Vector> >();
    }

    static PyObject * convert(const Vector & v) {
        //bpy::list list(v); // This segfaults :(
        bpy::list list;
        for (auto x : v) {
            list.append(x);
        }
        return bpy::incref(list.ptr());
    }
};


// https://stackoverflow.com/questions/42952781/how-to-wrap-a-c-class-with-a-constructor-that-takes-a-stdmap-or-stdvector

template <typename Map>
struct dict_to_map {

    typedef typename Map::key_type K;
    typedef typename Map::mapped_type V;

    // Constructor
    // Registers the converter with the Boost.Python runtime
    dict_to_map() {
        bpy::converter::registry::push_back(
            &convertible,
            &construct,
            bpy::type_id<Map>()
#ifdef BOOST_PYTHON_SUPPORTS_PY_SIGNATURES
            , &bpy::converter::wrap_pytype<&PyDict_Type>::get_pytype
#endif
        );
    }

    // Check if conversion is possible
    static void * convertible(PyObject * obj_ptr) {
        return PyDict_Check(obj_ptr) ? obj_ptr : nullptr;
    }

    /// Perform the conversion
    static void construct(
        PyObject * obj_ptr,
        bpy::converter::rvalue_from_python_stage1_data * data
    ) {
        // Convert the PyObject pointed to by `obj_ptr` to a dict
        bpy::handle<> objhandle{ bpy::borrowed(obj_ptr) };   // "smart ptr"
        bpy::dict d{ objhandle };

        // Get a pointer to memory into which we construct the map
        // This is provided by the Python runtime
        void * storage = reinterpret_cast<
            bpy::converter::rvalue_from_python_storage<Map> *
        >(data)->storage.bytes;

        // Placement-new allocate the result
        new(storage) Map{};
        Map& m{ *(static_cast<Map *>(storage)) };

        // Iterate over the dictionary `d`, fill up the map `m`
        bpy::list keys{ d.keys() };
        int num_keys{ static_cast<int>(bpy::len(keys)) };
        for (int i = 0; i < num_keys; ++i) {
            // Get the key
            bpy::object key_obj{ keys[i] };
            bpy::extract<K> key_proxy{ key_obj };
            if (!key_proxy.check()) {
                PyErr_SetString(PyExc_KeyError, "Bad key type");
                bpy::throw_error_already_set();
            }
            K key = key_proxy();

            // Get the corresponding value
            bpy::object val_obj{ d[key_obj] };
            bpy::extract<V> val_proxy{ val_obj };
            if (!val_proxy.check()) {
                PyErr_SetString(PyExc_ValueError, "Bad value type");
                bpy::throw_error_already_set();
            }
            V val = val_proxy();

            // Map key/value
            m[key] = val;
        }

        // Remember the location for later
        data->convertible = storage;
    }
};

template <typename Vector>
struct list_to_vector {

    // The type of the vector we convert the Python list into
    typedef typename Vector::value_type T;

    // Constructor
    // Registers the converter
    list_to_vector() {
        bpy::converter::registry::push_back(
            &convertible,
            &construct,
            bpy::type_id<Vector>()
#ifdef BOOST_PYTHON_SUPPORTS_PY_SIGNATURES
            , &bpy::converter::wrap_pytype<&PyList_Type>::get_pytype
#endif
        );
    }

    /// Check if conversion is possible
    static void * convertible(PyObject * obj_ptr) {
        return PyList_Check(obj_ptr) ? obj_ptr : nullptr;
    }

    /// Perform the conversion
    static void construct(
        PyObject * obj_ptr,
        bpy::converter::rvalue_from_python_stage1_data * data
    ) {
        // Convert the PyObject pointed to by `obj_ptr` to a bpy::list
        bpy::handle<> objhandle{ bpy::borrowed(obj_ptr) };   // "smart ptr"
        bpy::list lst{ objhandle };

        // Get a pointer to memory into which we construct the vector
        // This is provided by the Python side somehow
        void* storage = reinterpret_cast<
            bpy::converter::rvalue_from_python_storage<Vector> *
        >(data)->storage.bytes;

        // Placement-new allocate the result
        new(storage) Vector{};
        Vector & vec{ *(static_cast<Vector *>(storage)) };

        // Iterate over the list `lst`, fill up the vector `vec`
        int num_elements{ static_cast<int>(bpy::len(lst)) };
        for (int i = 0; i < num_elements; ++i) {
            // Get the element
            bpy::object elem_obj{ lst[i] };
            bpy::extract<T> elem_proxy{ elem_obj };
            if (! elem_proxy.check()) {
                PyErr_SetString(PyExc_ValueError, "Bad element type");
                bpy::throw_error_already_set();
            }
            T elem = elem_proxy();
            vec.push_back(elem);
        }

        // Remember the location for later
        data->convertible = storage;
    }
};

#endif
