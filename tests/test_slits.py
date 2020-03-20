import logging
from unittest.mock import Mock

import pytest
from ophyd.sim import make_fake_device
from pcdsdevices.slits import Slits

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_slits():
    FakeSlits = make_fake_device(Slits)
    slits = FakeSlits("TST:JAWS:", name='Test Slits')
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
    assert status.done and status.success


def test_slit_subscriptions(fake_slits):
    logger.debug('test_slit_subscriptions')
    slits = fake_slits
    # Subscribe a pseudo callback
    cb = Mock()
    slits.subscribe(cb, event_type=slits.SUB_STATE, run=False)
    # Change the aperture size
    slits.xwidth.readback.sim_put(40.0)
    assert cb.called


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
    slits.unstage()
    assert slits.xwidth.setpoint.get() == 2.5
    assert slits.ywidth.setpoint.get() == 2.5


@pytest.mark.timeout(5)
def test_slits_disconnected():
    Slits("TST:JAWS:", name='Test Slits')
