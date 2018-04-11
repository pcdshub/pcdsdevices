import time

import pytest

from pcdsdevices.epics_motor import PCDSMotorBase, IMS
from pcdsdevices.sim.pv import using_fake_epics_pv
from .conftest import attr_wait_value


def fake_motor():
    m = PCDSMotorBase("Tst:MMS:02", name='Test Motor')
    m.limits = (-100, 100)
    # Wait for threads to finish
    attr_wait_value(m, 'low_limit', -100)
    attr_wait_value(m, 'high_limit', 100)
    m.wait_for_connection()
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


@using_fake_epics_pv
def test_ims_clear_flag():
    # Instantiate motor
    m = IMS('Tst:Mtr:1', name='motor')
    m.wait_for_connection()
    # Already cleared
    m.bit_status._read_pv.put(0)
    m.clear_all_flags()
    # Clear a specific flag
    m.bit_status._read_pv.put(4194304)  # 2*22
    time.sleep(0.5)
    st = m.clear_stall(wait=False)
    assert m.seq_seln.get() == 40
    # Status should not be done until error goes away
    assert not st.done
    assert not st.success
    m.bit_status._read_pv.put(0)
    m.bit_status._read_pv.run_callbacks()
    assert st.done
    assert st.success


@using_fake_epics_pv
def test_ims_reinitialize():
    m = IMS('Tst:Mtr:1', name='motor')
    m.wait_for_connection()
    m.reinit_command.put(0)
    # Do not reinitialize on auto-setup
    m.error_severity._read_pv.put(0)
    m.auto_setup()
    assert m.reinit_command.get() == 0
    # Check that we reinitialize
    m.error_severity._read_pv.put(3)
    st = m.reinitialize(wait=False)
    assert m.reinit_command.get() == 1
    # Status should not be complete until reinitialize is done
    assert not st.done
    assert not st.success
    # When error severity returns to 3 we are reinitialized
    m.error_severity._read_pv.put(0)
    m.error_severity._read_pv.run_callbacks()
    time.sleep(1.0)
    assert st.done
    assert st.success
