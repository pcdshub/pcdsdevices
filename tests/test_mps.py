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
from pcdsdevices.epics.mps import MPS, mps_factory

from .conftest import attr_wait_true

def fake_mps():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    return MPS("TST:MPS")


@using_fake_epics_pv
def test_mps_faults():
    mps = fake_mps()
    #Faulted
    mps.fault._read_pv.put(1)
    mps.bypass._read_pv.put(0)
    assert mps.faulted
    #Faulted but bypassed
    mps.bypass._read_pv.put(1)
    assert mps.bypassed
    assert not mps.faulted

@using_fake_epics_pv
def test_mps_subscriptions():
    mps = fake_mps()
    #Subscribe a pseudo callback
    cb = Mock()
    mps.subscribe(cb, run=False)
    #Cause a fault
    mps.fault._read_pv.put(1)
    attr_wait_true(cb, 'called')
    assert cb.called

@using_fake_epics_pv
def test_mps_factory():
    mps = fake_mps()
    #Create a custom device
    class MyDevice(Device):
        pass
    #Create a constructor for the MPS version of that device
    MPSDevice = partial(mps_factory, 'MPSDevice', MyDevice)
    #Create an instanace of the MPSDevice
    d = MPSDevice('Tst:Prefix', name='Tst', mps_prefix='Tst:Mps:Prefix')
    #Check we made an MPS subcomponent
    assert hasattr(d, 'mps')
    assert isinstance(d.mps, MPS)
    assert d.mps.prefix == 'Tst:Mps:Prefix'
    #Check our original device constructor still worked
    assert d.name == 'Tst'
