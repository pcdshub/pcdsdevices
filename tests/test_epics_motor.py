import pytest

from pcdsdevices.epics_motor import PCDSMotorBase
from pcdsdevices.sim.pv import using_fake_epics_pv
from .conftest import attr_wait_value

def fake_motor():
    m = PCDSMotorBase("Tst:MMS:02", name='Test Motor')
    m.limits = (-100, 100)
    # Wait for threads to finish
    attr_wait_value(m, 'low_limit', -100)
    attr_wait_value(m, 'high_limit', 100)
    return m

@using_fake_epics_pv
def test_epics_motor_soft_limits():
    m = fake_motor()
    # Check that our limits were set correctly
    assert m.limits == (-100, 100)
    # Check that we can not move past the soft limits
    with pytest.raises(ValueError):
        m.move(-150)
    with pytest.raises(ValueError):
        m.move(None)

@using_fake_epics_pv
def test_epics_motor_tdir():
    m = fake_motor()
    # Simulate a moving motor
    m._pos_changed(value=-1.0, old_value=0.0)
    assert m.direction_of_travel.get() == 0
    m._pos_changed(value=2.0, old_value=-1.0)
    assert m.direction_of_travel.get() == 1



