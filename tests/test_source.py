#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
from collections import OrderedDict

##########
# Module #
##########
from pcdsdevices.sim.source import Undulator

def test_Undulator_instantiates():
    assert(Undulator("TEST"))

def test_Undulator_runs_ophyd_functions():
    und = Undulator("TEST")
    assert(isinstance(und.read(), OrderedDict))
    assert(isinstance(und.describe(), OrderedDict))
    assert(isinstance(und.describe_configuration(), OrderedDict))
    assert(isinstance(und.read_configuration(), OrderedDict))

