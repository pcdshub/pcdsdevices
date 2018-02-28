from collections import OrderedDict

from pcdsdevices.sim.areadetector.cam import (CamBase, PulnixCam)

# CamBase Tests

def test_CamBase_instantiates():
    assert(CamBase("TEST", name="test"))

def test_CamBase_runs_ophyd_functions():
    cam = CamBase("TEST", name="test")
    assert(isinstance(cam.read(), OrderedDict))
    assert(isinstance(cam.describe(), OrderedDict))
    assert(isinstance(cam.describe_configuration(), OrderedDict))
    assert(isinstance(cam.read_configuration(), OrderedDict))

# PulnixCam Tests

def test_PulnixCam_instantiates():
    assert(PulnixCam("TEST", name="test"))

def test_PulnixCam_runs_ophyd_functions():
    pulnix = PulnixCam("TEST", name="test")
    assert(isinstance(pulnix.read(), OrderedDict))
    assert(isinstance(pulnix.describe(), OrderedDict))
    assert(isinstance(pulnix.describe_configuration(), OrderedDict))
    assert(isinstance(pulnix.read_configuration(), OrderedDict))

