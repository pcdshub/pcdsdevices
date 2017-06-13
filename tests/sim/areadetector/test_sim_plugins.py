#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
from collections import OrderedDict
##########
# Module #
##########
from pcdsdevices.sim.areadetector.plugins import (PluginBase, StatsPlugin)
# PluginBase Tests

def test_PluginBase_instantiates():
    assert(PluginBase("TEST"))

def test_PluginBase_runs_ophyd_functions():
    plugin = PluginBase("TEST")
    assert(isinstance(plugin.read(), OrderedDict))
    assert(isinstance(plugin.describe(), OrderedDict))
    assert(isinstance(plugin.describe_configuration(), OrderedDict))
    assert(isinstance(plugin.read_configuration(), OrderedDict))

# StatsPlugin Tests

def test_StatsPlugin_instantiates():
    assert(StatsPlugin("TEST"))

def test_StatsPlugin_runs_ophyd_functions():
    plugin = StatsPlugin("TEST")
    assert(isinstance(plugin.read(), OrderedDict))
    assert(isinstance(plugin.describe(), OrderedDict))
    assert(isinstance(plugin.describe_configuration(), OrderedDict))
    assert(isinstance(plugin.read_configuration(), OrderedDict))
