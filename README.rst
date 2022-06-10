==================
Pattern clustering
==================


.. image:: https://img.shields.io/pypi/v/pattern_clustering.svg
        :target: https://pypi.python.org/pypi/pattern_clustering
        :alt: PyPI Status

.. image:: https://github.com/nokia/pattern-clustering/workflows/build/badge.svg?branch=main
        :target: https://github.com/nokia/pattern_clustering/actions?query=workflow%3Abuild
        :alt: Build Status

.. image:: https://github.com/nokia/pattern-clustering/workflows/docs/badge.svg?branch=main
        :target: https://github.com/nokia/pattern_clustering/actions?query=workflow%3Adocs
        :alt: Documentation Status


.. image:: https://codecov.io/gh/nokia/pattern-clustering/branch/main/graphs/badge.svg
        :target: https://codecov.io/gh/nokia/pattern-clustering/branch/main/graphs
        :alt: Code Coverage


This tool clusterizes lines of text given a collection of input patterns modeled using regular expressions.

This work has been published to:

[ICPR'2022] A novel pattern-based edit distance for automatic log parsing, Maxime Raynal, Marc-Olivier Buob, Georges Quénot.

--------
Features
--------

* Forms groups of homogeneous line using a pattern based distance, based on customizable patterns.
* Configured by default to use common patterns (IP addresses, numeric values, etc.) 

-------
License
-------

This project is licensed under the BSD-3-Clause license - see the `LICENSE <https://github.com/nokia/minifold/blob/master/LICENSE>`_.

-----------------------------
More about pattern-clustering
-----------------------------

.. _wiki: https://github.com/nokia/pattern-clustering/wiki
.. _Overview: https://github.com/nokia/pattern-clustering/wiki/Overview
.. _Installation: https://github.com/nokia/pattern-clustering/wiki/Installation
.. _Tests: https://github.com/nokia/pattern-clustering/wiki/Tests
.. _Tutorial: https://github.com/nokia/pattern-clustering/wiki/Tutorial
.. _Configuration: https://github.com/nokia/pattern-clustering/wiki/Configuration
.. _Packaging: https://github.com/nokia/pattern-clustering/wiki/Packaging

For more information, feel free to visit the wiki_:

- Overview_
- Installation_
- Tests_
- Tutorial_ 
- Configuration_
- Packaging_

-------
Acks
-------

The skeleton package was created with Cookiecutter_ and the `francois-durand/package_helper_2`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`francois-durand/package_helper_2`: https://github.com/francois-durand/package_helper_2
