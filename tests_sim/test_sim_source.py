from collections import OrderedDict

from pcdsdevices.sim.source import Undulator

def test_Undulator_instantiates():
    assert(Undulator("TEST", name="test"))

def test_Undulator_runs_ophyd_functions():
    und = Undulator("TEST", name="test")
    assert(isinstance(und.read(), OrderedDict))
    assert(isinstance(und.describe(), OrderedDict))
    assert(isinstance(und.describe_configuration(), OrderedDict))
    assert(isinstance(und.read_configuration(), OrderedDict))

