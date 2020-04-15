import logging

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import close_run, open_run, stage, unstage
from ophyd.sim import make_fake_device
from ophyd.status import wait as status_wait
from pcdsdevices.epics_motor import (IMS, PMC100, BeckhoffAxis, EpicsMotor,
                                     EpicsMotorInterface, Motor,
                                     MotorDisabledError, Newport,
                                     PCDSMotorBase)

logger = logging.getLogger(__name__)


def fake_class_setup(cls):
    """
    Make the fake class and modify if needed
    """
    FakeClass = make_fake_device(cls)
    return FakeClass


def motor_setup(motor):
    """
    Set up the motor based on the class
    """
    if isinstance(motor, EpicsMotorInterface):
        motor.user_readback.sim_put(0)
        motor.limits = (-100, 100)

    if isinstance(motor, PCDSMotorBase):
        motor.motor_spg.sim_put(2)
        motor.motor_spg.sim_set_enum_strs(['Stop', 'Pause', 'Go'])

    if isinstance(motor, IMS):
        motor.bit_status.sim_put(0)
        motor.part_number.sim_put('PN123')
        motor.error_severity.sim_put(0)
        motor.reinit_command.sim_put(0)


def fake_motor(cls):
    """
    Given a real class, lets get a fake motor
    """
    FakeCls = fake_class_setup(cls)
    motor = FakeCls('TST:MTR', name='test_motor')
    motor_setup(motor)
    return motor


# Here I set up fixtures that test each level's overrides
# Test in subclasses too to make sure we didn't break it!

@pytest.fixture(scope='function',
                params=[EpicsMotorInterface, PCDSMotorBase, IMS, Newport,
                        PMC100, BeckhoffAxis])
def fake_epics_motor(request):
    """
    Test EpicsMotorInterface and subclasses
    """
    return fake_motor(request.param)


@pytest.fixture(scope='function',
                params=[PCDSMotorBase, IMS, Newport, PMC100])
def fake_pcds_motor(request):
    """
    Test PCDSMotorBase and subclasses
    """
    return fake_motor(request.param)


@pytest.fixture(scope='function')
def fake_ims():
    """
    Test IMS-specific overrides
    """
    return fake_motor(IMS)


@pytest.fixture(scope='function')
def fake_beckhoff():
    """
    Test Beckhoff-specific overrides
    """
    return fake_motor(BeckhoffAxis)


def test_epics_motor_soft_limits(fake_epics_motor):
    logger.debug('test_epics_motor_soft_limits')
    m = fake_epics_motor
    # Check that our limits were set correctly
    assert m.limits == (-100, 100)
    # Check that we can not move past the soft limits
    with pytest.raises(ValueError):
        m.move(-150)


def test_epics_motor_tdir(fake_pcds_motor):
    logger.debug('test_epics_motor_tdir')
    m = fake_pcds_motor
    # Simulate a moving motor
    m._pos_changed(value=-1.0, old_value=0.0)
    assert m.direction_of_travel.get() == 0
    m._pos_changed(value=2.0, old_value=-1.0)
    assert m.direction_of_travel.get() == 1


def test_ims_clear_flag(fake_ims):
    logger.debug('test_ims_clear_flag')
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
    logger.debug('test_ims_reinitialize')
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
    logger.debug('test_ims_stage_in_plan')
    RE = RunEngine()
    m = fake_ims

    def plan():
        yield from open_run()
        yield from stage(m)
        yield from unstage(m)
        yield from close_run()

    RE(plan())


def test_spg_resume_pause_stop(fake_pcds_motor):
    logger.debug('test_resume_pause_stop')
    m = fake_pcds_motor
    m.spg_stop()
    assert m.motor_spg.get(as_string=True) == 'Stop'
    with pytest.raises(MotorDisabledError):
        m.check_value(10)
    with pytest.raises(MotorDisabledError):
        m.move(10, wait=False)
    m.spg_pause()
    assert m.motor_spg.get(as_string=True) == 'Pause'
    with pytest.raises(MotorDisabledError):
        m.move(10, wait=False)
    m.spg_go()
    assert m.motor_spg.get(as_string=True) == 'Go'
    # Test staging
    m.motor_spg.put(0)
    m.stage()
    assert m.motor_spg.get() == 2
    # Test unstaging
    m.unstage()
    assert m.motor_spg.get() == 0


def test_disable(fake_pcds_motor):
    logger.debug('test_disable')
    m = fake_pcds_motor
    m.disable()
    with pytest.raises(MotorDisabledError):
        m.check_value(1)
    with pytest.raises(MotorDisabledError):
        m.move(1, wait=False)
    m.enable()
    m.move(1, wait=False)


def test_beckhoff_error_clear(fake_beckhoff):
    m = fake_beckhoff
    m.clear_error()
    assert m.plc.cmd_err_reset.get() == 1
    m.stage()
    m.unstage()


def test_motor_factory():
    m = Motor('TST:MY:MMS:01', name='test_motor')
    assert isinstance(m, IMS)
    m = Motor('TST:RANDOM:MTR:01', name='test_motor')
    assert isinstance(m, EpicsMotor)


@pytest.mark.parametrize("cls", [PCDSMotorBase, IMS, Newport, PMC100,
                                 BeckhoffAxis, EpicsMotor])
@pytest.mark.timeout(5)
def test_disconnected_motors(cls):
    cls('MOTOR', name='motor')
