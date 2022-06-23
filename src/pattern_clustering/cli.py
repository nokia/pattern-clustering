#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

"""Console script for pattern_clustering."""

__author__     = "Marc-Olivier Buob, Maxime Raynal"
__maintainer__ = "Marc-Olivier Buob, Maxime Raynal"
__email__      = "marc-olivier.buob@nokia-bell-labs.com, maxime.raynal@nokia.com"
__copyright__  = "Copyright (C) 2022, Nokia"
__license__    = "BSD-3"

import argparse
import sys


def main():
    """Console script for pattern_clustering."""
    parser = argparse.ArgumentParser()
    parser.add_argument('_', nargs='*')
    args = parser.parse_args()

    print("Arguments: " + str(args._))
    print("Replace this message by putting your code into "
          "pattern_clustering.cli.main")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
