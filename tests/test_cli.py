#!/usr/bin/env pytest
# -*- coding: utf-8 -*-
#
# This file is part of the pattern-clustering project.
# https://github.com/nokia/pattern-clustering

__author__     = "Marc-Olivier Buob"
__maintainer__ = "Marc-Olivier Buob"
__email__      = "marc-olivier.buob@nokia-bell-labs.com"
__copyright__  = "Copyright (C) 2023, Nokia"
__license__    = "Nokia"

import json
import subprocess
from pattern_clustering.cli import *

def test_message(capsys):
    msg = "hello"
    for f in message, warning, info:
        f(msg)
        captured = capsys.readouterr()
        assert msg in captured.err


def test_main_pattern_clustering_mkconf(capsys):
    main_pattern_clustering_mkconf()
    captured = capsys.readouterr()
    data = captured.out
    d = json.loads(data)
    assert set(d.keys()) == {"threshold", "patterns"}


def call(cmd: str) -> str:
    result = subprocess.check_output(cmd, shell=True)
    return result.strip().decode("utf-8")

def test_main_pattern_distance():
    w1 = "0.0.0.0         192.168.0.254   0.0.0.0         UG    600    0        0 wlp2s0"
    w2 = "192.168.0.0     0.0.0.0         255.255.255.0   U     600    0        0 wlp2s0"
    assert call(f"pattern-distance -n '{w1}' '{w2}'") == "0.007259624900493844"
