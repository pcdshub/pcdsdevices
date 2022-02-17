import logging
from functools import partial
from unittest.mock import Mock

import pytest
from ophyd import Device
from ophyd.sim import make_fake_device

from .. import mps as mps_module
from ..mps import MPS, MPSLimits, mps_factory, must_be_known, must_be_out

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_mps():
    FakeMPS = make_fake_device(MPS)
    # Hotpatch module to make the mps_factory behave
    mps_module.MPS = FakeMPS
    mps = FakeMPS("TST:MPS", name='MPS Bit')
    return mps


@pytest.fixture(scope='function')
def fake_mps_limits():
    FakeLimits = make_fake_device(MPSLimits)
    mps = FakeLimits("Tst:Mps:Lim", logic=lambda x, y: x, name='MPS Limits')
    # Not bypassed or faulted
    mps.in_limit.fault.sim_put(0)
    mps.in_limit.bypass.sim_put(0)
    mps.out_limit.fault.sim_put(0)
    mps.out_limit.bypass.sim_put(0)
    return mps


def test_must_be_out():
    logger.debug('test_must_be_out')
    assert not must_be_out(True, True)
    assert not must_be_out(True, False)
    assert must_be_out(False, True)
    assert not must_be_out(False, False)


def test_must_be_known():
    logger.debug('test_must_be_known')
    assert not must_be_known(True, True)
    assert must_be_known(True, False)
    assert must_be_known(False, True)
    assert not must_be_known(False, False)


def test_mps_faults(fake_mps):
    mps = fake_mps
    # Faulted
    mps.fault.sim_put(1)
    mps.bypass.sim_put(0)
    assert mps.faulted
    # Faulted but bypassed
    mps.bypass.sim_put(1)
    assert mps.bypassed
    assert mps.faulted
    assert not mps.tripped


def test_mps_subscriptions(fake_mps):
    mps = fake_mps
    # Subscribe a pseudo callback
    cb = Mock()
    mps.subscribe(cb, run=False)
    # Cause a fault
    mps.fault.sim_put(1)
    assert cb.called


def test_mps_factory(fake_mps):
    # Create a custom device
    class MyDevice(Device):
        pass
    # Create a constructor for the MPS version of that device
    MPSDevice = partial(mps_factory, 'MPSDevice', MyDevice)
    # Create an instanace of the MPSDevice
    d = MPSDevice('Tst:Prefix', name='Tst', mps_prefix='Tst:Mps:Prefix')
    # Check we made an MPS subcomponent
    assert hasattr(d, 'mps')
    assert isinstance(d.mps, MPS)
    assert d.mps.prefix == 'Tst:Mps:Prefix'
    # Check our original device constructor still worked
    assert d.name == 'Tst'


def test_mpslimit_faults(fake_mps_limits):
    mps = fake_mps_limits
    assert not mps.faulted
    mps.in_limit.fault.sim_put(1)
    assert mps.faulted
    mps.in_limit.bypass.sim_put(1)
    assert mps.faulted
    assert mps.bypassed
    assert not mps.tripped


def test_mpslimit_subscriptions(fake_mps_limits):
    mps = fake_mps_limits
    # Subscribe a pseudo callback
    cb = Mock()
    mps.subscribe(cb, run=False)
    # Cause a fault
    mps.out_limit.fault.sim_put(1)
    assert cb.called


@pytest.mark.timeout(5)
def test_mps_disconnected():
    MPS("TST:MPS", name='MPS Bit')


@pytest.mark.timeout(5)
def test_mps_limit_disconnected():
    MPSLimits("Tst:Mps:Lim", logic=lambda x, y: x, name='MPS Limits')
