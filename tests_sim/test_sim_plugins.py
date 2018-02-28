from collections import OrderedDict

import numpy as np

from pcdsdevices.sim.areadetector.plugins import (PluginBase, StatsPlugin,
                                                  ImagePlugin)

# PluginBase Tests

def test_PluginBase_instantiates():
    assert(PluginBase("TEST", name="test"))

def test_PluginBase_runs_ophyd_functions():
    plugin = PluginBase("TEST", name="test")
    assert(isinstance(plugin.read(), OrderedDict))
    assert(isinstance(plugin.describe(), OrderedDict))
    assert(isinstance(plugin.describe_configuration(), OrderedDict))
    assert(isinstance(plugin.read_configuration(), OrderedDict))

# StatsPlugin Tests

def test_StatsPlugin_instantiates():
    assert(StatsPlugin("TEST", name="test"))

def test_StatsPlugin_runs_ophyd_functions():
    plugin = StatsPlugin("TEST", name="test")
    assert(isinstance(plugin.read(), OrderedDict))
    assert(isinstance(plugin.describe(), OrderedDict))
    assert(isinstance(plugin.describe_configuration(), OrderedDict))
    assert(isinstance(plugin.read_configuration(), OrderedDict))

def test_StatsPlugin_noise():
    stats = StatsPlugin("TEST", name="test", noise_x=True, noise_y=True, 
                        noise_kwargs_x={"scale":5}, noise_kwargs_y={"scale":10}, 
                        noise_type_x="uni", noise_type_y="uni")
    stats.centroid.x.put(5)
    stats.centroid.y.put(10)    
    assert(stats.centroid.x.value != 5 and np.isclose(
        stats.centroid.x.value, 5, atol=5))
    assert(stats.centroid.y.value != 10 and np.isclose(
        stats.centroid.y.value, 10, atol=10))

def test_ImagePlugin_instantiates():
    assert(ImagePlugin("TEST", name="test"))
    
def test_ImagePlugin_runs_ophyd_functions():
    plugin = ImagePlugin("TEST", name="test")
    assert(isinstance(plugin.read(), OrderedDict))
    assert(isinstance(plugin.describe(), OrderedDict))
    assert(isinstance(plugin.describe_configuration(), OrderedDict))
    assert(isinstance(plugin.read_configuration(), OrderedDict))

def test_ImagePlugin_image_info_is_correct():
    plugin = ImagePlugin("TEST", name="test")
    test_array = np.zeros((1000,500, 3))
    plugin._image = lambda : test_array
    assert(plugin.image.all() == test_array.all())
    assert(plugin.array_pixels == 1000*500*3)    
    assert(plugin.array_data.value.all() == test_array.flatten().all())
    assert(plugin.array_size.height.value == 1000)
    assert(plugin.array_size.width.value == 500)
    assert(plugin.array_size.depth.value == 3)
