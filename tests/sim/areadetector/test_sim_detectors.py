#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
from collections import OrderedDict
##########
# Module #
##########
from pcdsdevices.sim.areadetector.detectors import (DetectorBase, 
                                                    PulnixDetector)

# DetectorBase Tests

def test_DetectorBase_instantiates():
    assert(DetectorBase("TEST"))

def test_DetectorBase_runs_ophyd_functions():
    det = DetectorBase("TEST")
    assert(isinstance(det.read(), OrderedDict))
    assert(isinstance(det.describe(), OrderedDict))
    assert(isinstance(det.describe_configuration(), OrderedDict))
    assert(isinstance(det.read_configuration(), OrderedDict))

# PulnixDetector Tests

def test_PulnixDetector_instantiates():
    assert(PulnixDetector("TEST"))

def test_PulnixDetector_runs_ophyd_functions():
    pulnix_det = PulnixDetector("TEST")
    assert(isinstance(pulnix_det.read(), OrderedDict))
    assert(isinstance(pulnix_det.describe(), OrderedDict))
    assert(isinstance(pulnix_det.describe_configuration(), OrderedDict))
    assert(isinstance(pulnix_det.read_configuration(), OrderedDict))

def test_PulnixDetector_cam_component_reads():
    pulnix_det = PulnixDetector("TEST")
    assert(isinstance(pulnix_det.cam.read(), OrderedDict))
