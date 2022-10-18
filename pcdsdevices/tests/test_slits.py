import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device

from ..slits import BeckhoffSlits, LusiSlits, SimLusiSlits

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_slits():
    FakeSlits = make_fake_device(LusiSlits)
    slits = FakeSlits("TST:JAWS:", name='Test Slits',
                      input_branches=['X0'], output_branches=['X0'])
    # Set centers
    slits.xcenter.readback.sim_put(0.0)
    slits.ycenter.readback.sim_put(0.0)
    # Set limits
    slits.xwidth.setpoint.sim_set_limits((-100.0, 100.0))
    slits.ywidth.setpoint.sim_set_limits((-100.0, 100.0))
    # Initialize dmov
    slits.xwidth.done.sim_put(0)
    slits.ywidth.done.sim_put(0)
    return slits


@pytest.fixture(scope='function')
def fake_beckhoff_slits():
    FakeBeckhoffSlits = make_fake_device(BeckhoffSlits)
    slits = FakeBeckhoffSlits('TST:BKSLITS', name='test_slits',
                              input_branches=['X0'], output_branches=['X0'])
    return slits


def test_slit_states(fake_slits):
    logger.debug('test_slit_states')
    slits = fake_slits
    # Wide open
    slits.xwidth.readback.sim_put(20.0)
    slits.ywidth.readback.sim_put(20.0)
    assert slits.removed
    assert not slits.inserted

    # Closed
    slits.xwidth.readback.sim_put(-5.0)
    slits.ywidth.readback.sim_put(-5.0)
    assert not slits.removed
    assert slits.inserted


def test_slit_motion(fake_slits):
    logger.debug('test_slit_motion')
    slits = fake_slits
    # Uneven motion
    status = slits.move((5.0, 10.0))
    assert slits.xwidth.setpoint.get() == 5.0
    assert slits.ywidth.setpoint.get() == 10.0
    assert not status.done
    # Manually complete move
    slits.xwidth.readback.sim_put(5.0)
    slits.xwidth.done.sim_put(1)
    slits.ywidth.readback.sim_put(10.0)
    slits.ywidth.done.sim_put(1)
    status.wait(timeout=1)
    assert status.done and status.success
    # Reset DMOV flags
    slits.xwidth.done.sim_put(0)
    slits.ywidth.done.sim_put(0)

    status = slits.remove(40.0)
    # Command was registered
    assert slits.xwidth.setpoint.get() == 40.0
    assert slits.ywidth.setpoint.get() == 40.0
    # Status object reports done at correct moment
    assert not status.done
    # Manually complete move
    slits.xwidth.readback.sim_put(40.0)
    slits.xwidth.done.sim_put(1)
    slits.ywidth.readback.sim_put(40.0)
    slits.ywidth.done.sim_put(1)
    status.wait(timeout=1)
    assert status.done and status.success


def test_slit_interface():
    logger.debug('test_slits_interface')
    slits = SimLusiSlits('SIM:SLIT', name='sim_slits')
    slits(3, 5)
    assert slits() == (3, 5)


def test_slit_subscriptions(fake_slits):
    logger.debug('test_slit_subscriptions')
    slits = fake_slits
    # Subscribe a pseudo callback
    cb = Mock()
    slits.xwidth.subscribe(cb, run=False)
    # Change the aperture size
    slits.xwidth.readback.sim_put(40.0)
    assert cb.called


@pytest.mark.timeout(10)
def test_slit_staging(fake_slits):
    logger.debug('test_slit_staging')
    slits = fake_slits
    # Check the starting location
    slits.xwidth.readback.sim_put(2.5)
    slits.ywidth.readback.sim_put(2.5)
    # Stage the slits to record the values
    slits.stage()
    # Check that unstage places everything back
    slits.xwidth.setpoint.sim_put(1.5)
    slits.ywidth.setpoint.sim_put(1.5)

    def x_done(*args, **kwargs):
        slits.xwidth.done.sim_put(0)
        slits.xwidth.done.sim_put(1)

    def y_done(*args, **kwargs):
        slits.ywidth.done.sim_put(0)
        slits.ywidth.done.sim_put(1)

    slits.xwidth.setpoint.subscribe(x_done)
    slits.ywidth.setpoint.subscribe(y_done)

    slits.unstage()
    assert slits.xwidth.setpoint.get() == 2.5
    assert slits.ywidth.setpoint.get() == 2.5


def test_beckhoffslits_dmov(fake_beckhoff_slits):
    logger.debug('test_beckhoffslits_dmov')
    sl = fake_beckhoff_slits

    def set_all(dmov):
        sl.done_top.sim_put(dmov)
        sl.done_bottom.sim_put(dmov)
        sl.done_north.sim_put(dmov)
        sl.done_south.sim_put(dmov)

    set_all(False)
    assert not sl.done_all.get()
    set_all(True)
    assert sl.done_all.get()
    sl.done_top.sim_put(False)
    assert not sl.done_all.get()


@pytest.mark.timeout(5)
def test_slits_disconnected():
    LusiSlits("TST:JAWS:", name='Test Slits')
    BeckhoffSlits('TST:BK', name='test_slits')
