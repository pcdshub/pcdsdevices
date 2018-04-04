import time

from unittest.mock import Mock
from ophyd.status import wait as status_wait

from pcdsdevices.sim.pv import using_fake_epics_pv
from pcdsdevices.slits import Slits

from .conftest import attr_wait_true, attr_wait_value


def fake_slits():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    slits = Slits("TST:JAWS:", name='Test Slits')
    # Set centers
    slits.xcenter.readback._read_pv.put(0.0)
    slits.ycenter.readback._read_pv.put(0.0)
    # Set limits
    slits.xwidth._limits = (-100.0, 100.0)
    slits.ywidth._limits = (-100.0, 100.0)
    slits.wait_for_connection()
    return slits


@using_fake_epics_pv
def test_slit_states():
    slits = fake_slits()
    # Wide open
    slits.xwidth.readback._read_pv.put(20.0)
    slits.ywidth.readback._read_pv.put(20.0)
    attr_wait_true(slits, 'removed')
    assert slits.removed
    assert not slits.inserted

    # Closed
    slits.xwidth.readback._read_pv.put(-5.0)
    slits.ywidth.readback._read_pv.put(-5.0)
    attr_wait_true(slits, 'inserted')
    assert not slits.removed
    assert slits.inserted


@using_fake_epics_pv
def test_slit_motion():
    slits = fake_slits()
    # Uneven motion
    status = slits.move((5.0, 10.0))
    assert slits.xwidth.setpoint._write_pv.get() == 5.0
    assert slits.ywidth.setpoint._write_pv.get() == 10.0
    assert not status.done
    # Manually complete move
    slits.xwidth.readback._read_pv.put(5.0)
    slits.xwidth.done._read_pv.put(1)
    slits.ywidth.readback._read_pv.put(10.0)
    slits.ywidth.done._read_pv.put(1)
    status_wait(status, timeout=5.0)
    assert status.done and status.success
    # Reset DMOV flags
    slits.xwidth.done._read_pv.put(0)
    slits.ywidth.done._read_pv.put(0)
    time.sleep(1.0)

    status = slits.remove(40.0)
    # Command was registered
    assert slits.xwidth.setpoint._write_pv.get() == 40.0
    assert slits.ywidth.setpoint._write_pv.get() == 40.0
    # Status object reports done at correct moment
    assert not status.done
    # Manually complete move
    slits.xwidth.readback._read_pv.put(40.0)
    slits.xwidth.done._read_pv.put(1)
    slits.ywidth.readback._read_pv.put(40.0)
    slits.ywidth.done._read_pv.put(1)
    status_wait(status, timeout=1)
    assert status.done and status.success


@using_fake_epics_pv
def test_slit_transmission():
    slits = fake_slits()
    # Set our nominal aperture
    slits.nominal_aperture = (5.0, 10.0)
    # Half-closed
    slits.xwidth.readback._read_pv.put(2.5)
    slits.ywidth.readback._read_pv.put(5.0)
    attr_wait_value(slits, 'transmission', 0.5)
    assert slits.transmission == 0.5
    # Quarter-closed making sure we are using min
    slits.ywidth.readback._read_pv.put(2.5)
    slits.xwidth.readback._read_pv.put(5.0)
    attr_wait_value(slits, 'transmission', 0.25)
    assert slits.transmission == 0.25
    # Nothing greater than 100%
    slits.xwidth.readback._read_pv.put(40.0)
    slits.ywidth.readback._read_pv.put(40.0)
    attr_wait_value(slits, 'transmission', 1.0)
    assert slits.transmission == 1.0


@using_fake_epics_pv
def test_slit_subscriptions():
    slits = fake_slits()
    # Subscribe a pseudo callback
    cb = Mock()
    slits.subscribe(cb, event_type=slits.SUB_STATE, run=False)
    # Change the aperture size
    slits.xwidth.readback._read_pv.put(40.0)
    attr_wait_true(cb, 'called')
    assert cb.called


@using_fake_epics_pv
def test_slit_staging():
    slits = fake_slits()
    # Check the starting location
    slits.xwidth.readback._read_pv.put(2.5)
    slits.ywidth.readback._read_pv.put(2.5)
    time.sleep(1)
    # Stage the slits to record the values
    slits.stage()
    # Check that unstage places everything back
    slits.xwidth.setpoint._read_pv.put(1.5)
    slits.ywidth.setpoint._read_pv.put(1.5)
    slits.unstage()
    time.sleep(1)
    assert slits.xwidth.setpoint._write_pv.get() == 2.5
    assert slits.ywidth.setpoint._write_pv.get() == 2.5
