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
from pcdsdevices.mps import MPS, MPSLimits, mps_factory, must_be_out, must_be_known

from .conftest import attr_wait_true

def fake_mps():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    mps = MPS("TST:MPS")
    mps.wait_for_connection()
    return mps

def fake_mps_limits():
    mps = MPSLimits("Tst:Mps:Lim", logic=lambda x,y: x, name='MPS Limits')
    mps.wait_for_connection()
    # Not bypassed or faulted
    mps.in_limit.fault._read_pv.put(0)
    mps.in_limit.bypass._read_pv.put(0)
    mps.out_limit.fault._read_pv.put(0)
    mps.out_limit.bypass._read_pv.put(0)
    return mps

def test_must_be_out():
    assert not must_be_out(True, True)
    assert not must_be_out(True, False)
    assert must_be_out(False, True)
    assert not must_be_out(False, False)

def test_must_be_known():
    assert not must_be_known(True, True)
    assert must_be_known(True, False)
    assert must_be_known(False, True)
    assert not must_be_known(False, False)

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
    assert mps.faulted
    assert not mps.tripped

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

@using_fake_epics_pv
def test_mpslimit_faults():
    mps = fake_mps_limits()
    assert not mps.faulted
    mps.in_limit.fault._read_pv.put(1)
    assert mps.faulted
    mps.in_limit.bypass._read_pv.put(1)
    assert mps.faulted
    assert mps.bypassed
    assert not mps.tripped

@using_fake_epics_pv
def test_mpslimit_subscriptions():
    mps = fake_mps_limits()
    #Subscribe a pseudo callback
    cb = Mock()
    mps.subscribe(cb, run=False)
    #Cause a fault
    mps.out_limit.fault._read_pv.put(1)
    attr_wait_true(cb, 'called')
    assert cb.called
