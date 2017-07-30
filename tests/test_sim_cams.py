#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
from collections import OrderedDict
##########
# Module #
##########
from pcdsdevices.sim.areadetector.cam import (CamBase, PulnixCam)

# CamBase Tests

def test_CamBase_instantiates():
    assert(CamBase("TEST"))

def test_CamBase_runs_ophyd_functions():
    cam = CamBase("TEST")
    assert(isinstance(cam.read(), OrderedDict))
    assert(isinstance(cam.describe(), OrderedDict))
    assert(isinstance(cam.describe_configuration(), OrderedDict))
    assert(isinstance(cam.read_configuration(), OrderedDict))

# PulnixCam Tests

def test_PulnixCam_instantiates():
    assert(PulnixCam("TEST"))

def test_PulnixCam_runs_ophyd_functions():
    pulnix = PulnixCam("TEST")
    assert(isinstance(pulnix.read(), OrderedDict))
    assert(isinstance(pulnix.describe(), OrderedDict))
    assert(isinstance(pulnix.describe_configuration(), OrderedDict))
    assert(isinstance(pulnix.read_configuration(), OrderedDict))

