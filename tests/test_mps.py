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

@using_fake_epics_pv
def test_mps_factory():
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
