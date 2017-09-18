############
# Standard #
############
import logging
import time

###############
# Third Party #
###############
import pytest
from unittest.mock import Mock

##########
# Module #
##########
from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.epics  import MPS

@using_fake_epics_pv
@pytest.fixture(scope='function')
def mps():
    return MPS("TST:MPS")


@using_fake_epics_pv
def test_mps_faults(mps):
    #Faulted
    mps.fault._read_pv.put(1)
    mps.bypass._read_pv.put(0)
    assert mps.faulted
    #Faulted but bypassed
    mps.bypass._read_pv.put(1)
    assert mps.bypassed
    assert not mps.faulted

@using_fake_epics_pv
def test_mps_subscriptions(mps):
    #Subscribe a pseudo callback
    cb = Mock()
    mps.subscribe(cb, run=False)
    #Cause a fault
    mps.fault._read_pv.put(1)
    assert cb.called


