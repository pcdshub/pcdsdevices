############
# Standard #
############
import time
import logging
from functools import partial

###############
# Third Party #
###############
import pytest
from ophyd import Device
from unittest.mock import Mock

##########
# Module #
##########
from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics.mps import MPS, mps_factory, MPSLimits, mustBeOpenLogic, mustKnowPositionLogic

from .conftest import attr_wait_true


def fake_mps():

    mps = MPSLimits("TST:MPSA", "TST:MPSB")
    return mps


@using_fake_epics_pv

def test_mps_faults():
    mpsLimits = fake_mps()
    #Faulted
    mpsLimits.mps_A.fault._read_pv.put(1)
    mpsLimits.mps_A.bypass._read_pv.put(0)
    assert mpsLimits.mps_A.faulted
    
    mpsLimits.mps_B.fault._read_pv.put(1)
    mpsLimits.mps_B.bypass._read_pv.put(0)
    assert mpsLimits.mps_B.faulted


    mustBeOpenLogic(mpsLimits.mps_A, mpsLimits.mps_B)
    mustKnowPositionLogic(mpsLimits.mps_A, mpsLimits.mps_B)

