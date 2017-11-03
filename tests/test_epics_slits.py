############
# Standard #
############

###############
# Third Party #
###############
import pytest
from unittest.mock import Mock

##########
# Module #
##########
from pcdsdevices.sim.pv import  using_fake_epics_pv
from pcdsdevices.epics import Slits

from .conftest import attr_wait_true

def fake_slits():
    """
    using_fake_epics_pv does cleanup routines after the fixture and before the
    test, so we can't make this a fixture without destabilizing our tests.
    """
    return Slits("TST:JAWS:")


@using_fake_epics_pv
def test_slit_states():
    slits = fake_slits()
    #Wide open
    slits.xwidth.readback._read_pv.put(20.0)
    slits.ywidth.readback._read_pv.put(20.0)
    assert slits.removed
    assert not slits.inserted

    #Closed
    slits.xwidth.readback._read_pv.put(-5.0)
    slits.ywidth.readback._read_pv.put(-5.0)
    assert not slits.removed
    assert slits.inserted


@using_fake_epics_pv
def test_slit_motion():
    slits = fake_slits()
    #Set limits
    slits.xwidth._limits = (-100.0, 100.0)
    slits.ywidth._limits = (-100.0, 100.0)
    status = slits.remove(40.0)
    #Command was registered
    assert slits.xwidth.setpoint._write_pv.get() == 40.0
    assert slits.ywidth.setpoint._write_pv.get() == 40.0
    #Status object reports done at correct moment
    assert not status.done
    #Manually complete move
    slits.xwidth.readback._read_pv.put(40.0)
    slits.xwidth.done._read_pv.put(1)
    slits.ywidth.readback._read_pv.put(40.0)
    slits.ywidth.done._read_pv.put(1)
    assert status.done and status.success

    #Too small of a remove request
    with pytest.raises(ValueError):
        slits.remove(width=-5.0)

@using_fake_epics_pv
def test_slit_transmission():
    slits = fake_slits()
    #Half-closed
    slits.nominal_aperature = 5.0
    slits.xwidth.readback._read_pv.put(2.5)
    slits.ywidth.readback._read_pv.put(2.5)
    assert slits.transmission == 0.5
    #Quarter-closed making sure we are using min
    slits.ywidth.readback._read_pv.put(1.25)
    assert slits.transmission == 0.25
    #Nothing greater than 100%
    slits.xwidth.readback._read_pv.put(40.0)
    slits.ywidth.readback._read_pv.put(40.0)
    assert slits.transmission == 1.0


@using_fake_epics_pv
def test_slit_subscriptions():
    slits = fake_slits()
    #Subscribe a pseudo callback
    cb = Mock()
    slits.subscribe(cb, event_type=slits.SUB_STATE, run=False)
    #Change the aperature size
    slits.xwidth.readback._read_pv.put(40.0)
    attr_wait_true(cb, 'called')
    assert cb.called
