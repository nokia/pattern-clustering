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

import json
import sys
from collections import defaultdict
from optparse import OptionParser
from pattern_clustering import (
    PatternClusteringEnv, pattern_clustering_to_html,
    pattern_clustering_with_preprocess, pattern_clustering_without_preprocess
)

def message(s: str):
    print(s, file=sys.stderr)

def warning(s: str):
    message(f"[WARNING] {s}")

def error(s: str):
    message(f"[ERROR] {s}")
    sys.exit(1)

def info(s: str):
    print(f"[INFO] {s}")

def main():
    """Console script for pattern_clustering."""
    parser = OptionParser(usage="usage: %prog [options] INPUT_FILENAME")
    parser.add_option(
        "-c", "--config",
        metavar = "CONFIG_FILENAME",
        type    = "str",
        dest    = "config_filename",
        help    = "Path to the JSON configuration file. Supersedes command-line parameters.",
        default = None
    )
    parser.add_option(
        "-H", "--html-file",
        metavar = "OUTPUT_FILENAME",
        type    = "str",
        dest    = "html_output_filename",
        help    = "Path to the output HTML file used for human readable results.",
        default = None
    )
    parser.add_option(
        "-i", "--input-file",
        metavar = "INPUT_FILENAME",
        type    = "str",
        dest    = "input_filename",
        help    = "Path to the input (log) file. Defaults to the standard input.",
        default = sys.stdin
    )
    parser.add_option(
        "-n", "--no-async",
        dest    = "no_async",
        help    = "Disable asynchronous computations.",
        action  = "store_true"
    )
    parser.add_option(
        "-o", "--output-file",
        metavar = "OUTPUT_FILENAME",
        type    = "str",
        dest    = "output_filename",
        help    = "Path to the JSON output file. Defaults to the standard output.",
        default = None
    )
    parser.add_option(
        "-p", "--with-preprocessing",
        dest    = "with_preprocessing",
        help    = "Automatically groups in the same cluster every line having the same pattern-level structure. This accelerates the computation but may lead to inaccurate clusters.",
        action  = "store_true"
    )
    parser.add_option(
        "-t", "--threshold",
        metavar = "THRESHOLD",
        type    = "float",
        dest    = "threshold",
        help    = "Threshold value used by the clustering, between 0.0 and 1.0. The lower the value, the smaller the clusters. Defaults to 0.6",
        default = 0.6
    )
    parser.add_option(
        "-v", "--verbose",
        dest    = "verbose",
        help    = "Verbose mode",
        action  = "store_true"
    )

    (options, args) = parser.parse_args()
    if args:
        warning(f"Ignored argument: {args}")

    # Load parameters
    verbose = options.verbose
    threshold = options.threshold
    conf = defaultdict()
    no_async = options.no_async

    if options.config_filename:
        if verbose:
            info(
                f"Loading parameters from {options.config_filename} configuration file."
                " Command-line parameters are superseded by those specified in the "
                "configuration file."
            )
        with open(config_filename) as f_conf:
            conf = json.load(f_conf)
        patterns = conf.get("patterns", None)
        if patterns:
            PatternClusteringEnv.patterns = patterns
        threshold = conf.get("threshold", threshold)
        no_async = conf.get("no_async", no_async)
    elif verbose:
        info(f"Using command-line and default parameters.")

    use_async = not options.no_async
    pattern_clustering = (
        pattern_clustering_with_preprocess if options.with_preprocessing else
        pattern_clustering_without_preprocess
    )

    # Verbose messages
    if verbose:
        info(f"threshold: {threshold}")
        info(f"env:\n{PatternClusteringEnv()}")
        info(f"pattern_clustering: {pattern_clustering}")

    with open(options.input_filename) as f_in:
        lines = [line.strip() for line in f_in.readlines()]
        map_row_cluster = pattern_clustering(
            lines,
            max_dist=threshold,
            use_async=use_async
        )

    if options.output_filename:
        if verbose:
            info(f"Writting results to {options.output_filename}")
        with open(options.output_filename, "w") as f_out:
            json.dump(map_row_cluster, fp=f_out)
    else:
        print(json.dumps(map_row_cluster))

    if options.html_output_filename:
        with open(options.html_output_filename, "w") as f_html:
            print(f"<html><body>{pattern_clustering_to_html(lines, map_row_cluster)}</body></html>", file=f_html)

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
