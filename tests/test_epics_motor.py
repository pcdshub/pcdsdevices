import pytest

from bluesky import RunEngine
from bluesky.plan_stubs import stage, unstage, open_run, close_run
from ophyd.sim import make_fake_device
from ophyd.status import wait as status_wait

from pcdsdevices.epics_motor import PCDSMotorBase, IMS

from .conftest import HotfixFakeEpicsSignal


@pytest.fixture(scope='function')
def fake_motor():
    FakeMotor = make_fake_device(PCDSMotorBase)
    FakeMotor.motor_spg.cls = HotfixFakeEpicsSignal
    m = FakeMotor("Tst:MMS:02", name='Test Motor')
    m.limits = (-100, 100)
    m.motor_spg.sim_put(2)
    m.motor_spg.sim_set_enum_strs(['Stop', 'Pause', 'Go'])
    return m


@pytest.fixture(scope='function')
def fake_ims():
    FakeIMS = make_fake_device(IMS)
    FakeIMS.motor_spg.cls = HotfixFakeEpicsSignal
    m = FakeIMS('Tst:Mtr:1', name='motor')
    m.bit_status.sim_put(0)
    m.part_number.sim_put('PN123')
    m.error_severity.sim_put(0)
    m.reinit_command.sim_put(0)
    m.motor_spg.sim_put(2)
    m.motor_spg.sim_set_enum_strs(['Stop', 'Pause', 'Go'])
    return m


def test_epics_motor_soft_limits(fake_motor):
    m = fake_motor
    # Check that our limits were set correctly
    assert m.limits == (-100, 100)
    # Check that we can not move past the soft limits
    with pytest.raises(ValueError):
        m.move(-150)


def test_epics_motor_tdir(fake_motor):
    m = fake_motor
    # Simulate a moving motor
    m._pos_changed(value=-1.0, old_value=0.0)
    assert m.direction_of_travel.get() == 0
    m._pos_changed(value=2.0, old_value=-1.0)
    assert m.direction_of_travel.get() == 1


def test_ims_clear_flag(fake_ims):
    m = fake_ims
    # Already cleared
    m.clear_all_flags()
    # Clear a specific flag
    m.bit_status.sim_put(4194304)  # 2*22
    st = m.clear_stall(wait=False)
    assert m.seq_seln.get() == 40
    # Status should not be done until error goes away
    assert not st.done
    assert not st.success
    m.bit_status.sim_put(0)
    assert st.done
    assert st.success


def test_ims_reinitialize(fake_ims):
    m = fake_ims
    # Do not reinitialize on auto-setup
    m.auto_setup()
    assert m.reinit_command.get() == 0
    # Check that we reinitialize
    m.error_severity.sim_put(3)
    st = m.reinitialize(wait=False)
    assert m.reinit_command.get() == 1
    # Status should not be complete until reinitialize is done
    assert not st.done
    assert not st.success
    # When error severity is no longer 3 we are reinitialized
    m.error_severity.sim_put(0)
    status_wait(st)
    assert st.done
    assert st.success


def test_ims_stage_in_plan(fake_ims):
    RE = RunEngine()
    m = fake_ims

    def plan():
        yield from open_run()
        yield from stage(m)
        yield from unstage(m)
        yield from close_run()

    RE(plan())


def test_resume_pause_stop(fake_motor):
    m = fake_motor
    m.stop()
    assert m.motor_spg.get(as_string=True) == 'Stop'
    with pytest.raises(Exception):
        m.check_value(10)
    with pytest.raises(Exception):
        m.move(10, wait=False)
    m.pause()
    assert m.motor_spg.get(as_string=True) == 'Pause'
    with pytest.raises(Exception):
        m.move(10, wait=False)
    m.go()
    assert m.motor_spg.get(as_string=True) == 'Go'
    m.check_value(10)
    m.resume()
    assert m.motor_spg.get(as_string=True) == 'Go'
    m.check_value(10)
