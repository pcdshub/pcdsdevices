#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
from collections import OrderedDict
###############
# Third Party #
###############
import numpy as np
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
    # import ipdb; ipdb.set_trace()

    assert(StatsPlugin("TEST"))

def test_StatsPlugin_runs_ophyd_functions():
    plugin = StatsPlugin("TEST")
    assert(isinstance(plugin.read(), OrderedDict))
    assert(isinstance(plugin.describe(), OrderedDict))
    assert(isinstance(plugin.describe_configuration(), OrderedDict))
    assert(isinstance(plugin.read_configuration(), OrderedDict))

def test_StatsPlugin_noise():
    stats = StatsPlugin("TEST", noise_x=True, noise_y=True, 
                        noise_kwargs_x={"scale":5}, noise_kwargs_y={"scale":10}, 
                        noise_type_x="uni", noise_type_y="uni")
    stats.centroid.x.put(5)
    stats.centroid.y.put(10)    
    assert(stats.centroid.x.value != 5 and np.isclose(
        stats.centroid.x.value, 5, atol=5))
    assert(stats.centroid.y.value != 10 and np.isclose(
        stats.centroid.y.value, 10, atol=10))
