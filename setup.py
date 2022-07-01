#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

__author__     = "Marc-Olivier Buob"
__maintainer__ = "Marc-Olivier Buob"
__email__      = "marc-olivier.buob@nokia-bell-labs.com"
__copyright__  = "Copyright (C) 2022, Nokia"
__license__    = "BSD-3"


"""The setup script."""

import os, platform
from setuptools     import setup, find_packages, Extension
#from distutils.core import Extension
from setup_cpp      import find_cpp_sources

headers_dir = "boost"
sources_dir = "boost"
sources = find_cpp_sources(
    use_pyplusplus=False,
    sources_ext="cpp",
    headers_ext="hpp",
    headers_dir=headers_dir,
    sources_dir=sources_dir
)

# https://stackoverflow.com/questions/20872698/place-boost-python-extension-inside-package
cxx_flags = ["-std=c++11", "-W", "-Wall"]
(x, y, z) = platform.python_version().split(".")
lib_boost = f"boost_python{x}{y}"
lib_python = f"python{x}.{y}"

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = []
setup_requirements = ["pytest-runner",]
test_requirements = ["pytest>=3",]

setup(
    author="Marc-Olivier Buob, Maxime Raynal",
    author_email="marc-olivier.buob@nokia-bell-labs.com, maxime.raynal@nokia.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3"
    ],
    description="This tool clusterizes lines of text given a collection of input patterns modeled using regular "
                "expressions.",
    entry_points={
        "console_scripts": [
            "pattern-clustering-mkconf=pattern_clustering.cli:main_pattern_clustering_mkconf",
            "pattern-clustering=pattern_clustering.cli:main_pattern_clustering",
            "pattern-distance=pattern_clustering.cli:main_pattern_distance",
        ],
    },
    ext_modules=[
        Extension(
            # The extension MUST have the name of the package AND be in the package
            # https://stackoverflow.com/a/58857904/14851404
            # The generated .so that may directly be imported in python3
            "pattern_clustering.pattern_clustering",
            # The following macros remove some irrelevant compilation warnings.
            define_macros=[
                ("BOOST_BIND_GLOBAL_PLACEHOLDERS", None),
                ("BOOST_ALLOW_DEPRECATED_HEADERS", None),
            ],
            sources=sources,
            extra_compile_args=cxx_flags,
            extra_link_args=cxx_flags,
            include_dirs=["../../boost", os.path.dirname(os.path.abspath(__file__))],
            libraries=[lib_boost]
        )
    ],
    install_requires=requirements,
    license="BSD license",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
    include_package_data=True,
    keywords="pattern_clustering",
    name="pattern_clustering",
    # https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure
    packages=find_packages("src"),
    package_dir={'': 'src'},
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/nokia/pattern-clustering",
    version='1.0.0', # Use single quotes, see https://github.com/oceanprotocol/ocean.py/issues/194
    zip_safe=False,
)
