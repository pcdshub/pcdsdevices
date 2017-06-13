#!/usr/bin/env python
# -*- coding: utf-8 -*-
############
# Standard #
############
import time
from collections import OrderedDict

###############
# Third Party #
###############
import numpy as np

##########
# Module #
##########
from pcdsdevices.sim.pim import (PIMPulnixDetector, PIMMotor, PIM)

# PIMPulnixDetector Tests

def test_PIMPulnixDetector_instantiates():
    assert(PIMPulnixDetector("TEST"))

def test_PIMPulnixDetector_runs_ophyd_functions():
    pim_pulnix_det = PIMPulnixDetector("TEST")
    assert(isinstance(pim_pulnix_det.read(), OrderedDict))
    assert(isinstance(pim_pulnix_det.describe(), OrderedDict))
    assert(isinstance(pim_pulnix_det.describe_configuration(), OrderedDict))
    assert(isinstance(pim_pulnix_det.read_configuration(), OrderedDict))

def test_PIMPulnixDetector_stats_plugin_reads():
    pim_pulnix_det = PIMPulnixDetector("TEST")
    assert(isinstance(pim_pulnix_det.stats2.read(), OrderedDict))

# PIMMotor Tests

def test_PIMMotor_instantiates():
    assert(PIMMotor("TEST"))

def test_PIMMotor_runs_ophyd_functions():
    pmotor = PIMMotor("TEST")
    assert(isinstance(pmotor.read(), OrderedDict))
    assert(isinstance(pmotor.describe(), OrderedDict))
    assert(isinstance(pmotor.describe_configuration(), OrderedDict))
    assert(isinstance(pmotor.read_configuration(), OrderedDict))

def test_PIMMotor_transitions_states_correctly():
    pmotor = PIMMotor("TEST")
    status = pmotor.move("OUT")
    assert(pmotor.position == "OUT")
    assert(status.success)
    status = pmotor.move("IN")
    assert(pmotor.position == "IN")
    assert(status.success)
    status = pmotor.move("DIODE")
    assert(pmotor.position == "DIODE")
    assert(status.success)

# PIM Tests

def test_PIM_instantiates():
    assert(PIM("TEST"))

def test_PIM_runs_ophyd_functions():
    pim = PIM("TEST")
    assert(isinstance(pim.read(), OrderedDict))
    assert(isinstance(pim.describe(), OrderedDict))
    assert(isinstance(pim.describe_configuration(), OrderedDict))
    assert(isinstance(pim.read_configuration(), OrderedDict))
    
def test_PIM_has_centroid():
    pim = PIM("TEST")
    assert(isinstance(pim.detector.stats2.centroid.x.read(), dict))
    assert(isinstance(pim.detector.stats2.centroid.y.read(), dict))
    
def test_PIM_fake_sleep_move_time():
    pim = PIM("TEST")
    pim.move("OUT")
    pim.fake_sleep = 1
    t0 = time.time()
    status = pim.move("IN")
    t1 = time.time() - t0
    assert(np.isclose(t1, pim.fake_sleep + 0.1, rtol=0.1))
    assert(pim.position == "IN")
    assert(status.success)
