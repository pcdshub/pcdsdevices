import itertools
import logging

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import close_run, open_run, stage, unstage
from ophyd.sim import make_fake_device
from ophyd.status import MoveStatus
from ophyd.status import wait as status_wait
from ophyd.utils.epics_pvs import AlarmSeverity, AlarmStatus
from ophyd.utils.errors import LimitError

from ..epics_motor import (IMS, MMC100, PMC100, BeckhoffAxis, EpicsMotor,
                           EpicsMotorInterface, Motor, MotorDisabledError,
                           Newport, OffsetIMSWithPreset, OffsetMotor,
                           PCDSMotorBase)

logger = logging.getLogger(__name__)


def fake_class_setup(cls):
    """
    Make the fake class and modify if needed
    """
    FakeClass = make_fake_device(cls)
    # Recover subscription decorator behavior on motor class
    for name, cpt in FakeClass._sig_attrs.items():
        source_cpt = getattr(FakeClass.mro()[1], name)
        cpt._subscriptions.update(
            source_cpt._subscriptions
        )
    return FakeClass


def motor_setup(motor):
    """
    Set up the motor based on the class
    """
    if isinstance(motor, EpicsMotorInterface):
        motor.user_readback.sim_put(0)
        motor.high_limit_travel.put(100)
        motor.low_limit_travel.put(-100)
        motor.user_setpoint.sim_set_limits((-100, 100))
        motor.velocity.sim_put(10)

    if isinstance(motor, PCDSMotorBase):
        motor.motor_spg.sim_put(2)
        motor.motor_spg.sim_set_enum_strs(['Stop', 'Pause', 'Go'])

    if isinstance(motor, IMS):
        motor.bit_status.sim_put(0)
        motor.part_number.sim_put('PN123')
        motor.error_severity.sim_put(0)
        motor.reinit_command.sim_put(0)


def fake_motor(cls, name='test_motor'):
    """
    Given a real class, lets get a fake motor
    """
    FakeCls = fake_class_setup(cls)
    motor = FakeCls('TST:MTR', name=name)
    motor_setup(motor)
    return motor


# Here I set up fixtures that test each level's overrides
# Test in subclasses too to make sure we didn't break it!

@pytest.fixture(scope='function',
                params=[EpicsMotorInterface, PCDSMotorBase, IMS, Newport,
                        MMC100, PMC100, BeckhoffAxis])
def fake_epics_motor(request):
    """
    Test EpicsMotorInterface and subclasses
    """
    return fake_motor(request.param, name=f'mot_{request.node.name}')


@pytest.fixture(scope='function',
                params=[PCDSMotorBase, IMS, Newport, MMC100, PMC100])
def fake_pcds_motor(request):
    """
    Test PCDSMotorBase and subclasses
    """
    return fake_motor(request.param, name=f'mot_{request.node.name}')


@pytest.fixture(scope='function')
def fake_ims(request):
    """
    Test IMS-specific overrides
    """
    return fake_motor(IMS, name=f'mot_{request.node.name}')


@pytest.fixture(scope='function')
def fake_beckhoff(request):
    """
    Test Beckhoff-specific overrides
    """
    return fake_motor(BeckhoffAxis, name=f'mot_{request.node.name}')


@pytest.fixture(scope='function')
def fake_offset_ims():
    off_ims = make_fake_device(OffsetMotor)('FAKE:OFFSET:IMS',
                                            motor_prefix='MOTOR:PREFIX',
                                            name='fake_offset_ims')
    motor_setup(off_ims.motor)
    # start with motor position at 1
    off_ims.motor.user_readback.sim_put(1)
    return off_ims


@pytest.fixture(scope='function')
def fake_offset_ims_with_preset():
    off_ims = make_fake_device(OffsetIMSWithPreset)(
        'OFFSET:IMS:WITH:PRESET',
        motor_prefix='MOTOR:PREFIX',
        name='fake_offset_ims_with_preset')

    motor_setup(off_ims.motor)
    # start with motor position at 1
    off_ims.motor.user_readback.sim_put(1)
    return off_ims


def test_epics_motor_soft_limits(fake_epics_motor):
    logger.debug('test_epics_motor_soft_limits')
    m = fake_epics_motor
    # Check that our limits were set correctly
    assert m.limits == (-100, 100)
    assert m.get_low_limit() == -100
    assert m.get_high_limit() == 100
    # Check that we can not move past the soft limits
    with pytest.raises(ValueError):
        m.move(-150)
    # Try to move to a valid position
    m.move(60, wait=False)
    # move current position to -150
    m.user_readback.sim_put(-150)
    # Try to set low limit to higher than current position
    with pytest.raises(ValueError):
        # current position: -150
        m.set_low_limit(-101)
    # move current position to 150
    m.user_readback.sim_put(150)
    # Try to set low limit to lower than the current
    # position but higher than high limit.
    with pytest.raises(ValueError):
        # current high limit: 100
        # current position: 150
        m.set_low_limit(120)
    # Try to set hi limit to lower than current position
    with pytest.raises(ValueError):
        # current position: 150
        m.set_high_limit(90)
    # Try to set high limit to higher than the current
    # position but lower than low limit.
    # change the current position to -110
    m.user_readback.sim_put(-110)
    with pytest.raises(ValueError):
        # current low limit: -100
        # current position: -110
        m.set_high_limit(-105)
    # change the current position to 50
    m.user_readback.sim_put(50)
    # Try to successfully set the high and low limits:
    # current low limit: -100
    # current high limit: 100
    # current position:  50
    m.set_low_limit(-110)
    m.set_high_limit(110)
    m.check_value(42)
    assert m.get_low_limit() == -110
    assert m.get_high_limit() == 110


def test_clearing_limits(fake_epics_motor):
    m = fake_epics_motor
    # current limits: -100, 100
    assert m.get_low_limit() == -100
    assert m.get_high_limit() == 100
    m.clear_limits()
    assert m.get_low_limit() == 0
    assert m.get_high_limit() == 0


def test_limits_update_from_epics(fake_epics_motor: EpicsMotorInterface):
    mot = fake_epics_motor
    for low, high in (
        (-10, 10),
        (-100, 100),
        (0, 100),
        (-100, 0),
    ):
        mot.high_limit_travel.put(high)
        mot.low_limit_travel.put(low)
        for num in range(low + 1, high):
            mot.check_value(num)
        for num in itertools.chain(
            range(low - 10, low),
            range(high + 1, high + 10),
        ):
            with pytest.raises(LimitError):
                mot.check_value(num)
                # debug only hit if the check_value doesn't raise
                logger.debug(f'{low} < {num} < {high}')
                logger.debug(f'limits are {mot.limits}')
                logger.debug(f'LLM={mot.low_limit_travel.get()}')
                logger.debug(f'HLM={mot.high_limit_travel.get()}')
                logger.debug(f'md={mot.user_setpoint.metadata}')


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
    st.wait(timeout=1)
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


def test_beckhoff_velo_error(fake_beckhoff):
    mot = fake_beckhoff
    # Zero velo move fails silently if we don't catch it here
    mot.velocity.sim_put(0)
    low_limit = mot.low_limit_travel.get()
    high_limit = mot.high_limit_travel.get()
    for num in range(low_limit + 1, high_limit):
        with pytest.raises(RuntimeError):
            mot.check_value(num)

    with pytest.raises(RuntimeError):
        mot.move((low_limit + high_limit) / 2, wait=False)


def test_beckhoff_error_status(fake_beckhoff: BeckhoffAxis):
    # Helper
    def sim_move(dest: float, error: str = '', code: int = 0) -> MoveStatus:
        status = fake_beckhoff.move(dest, wait=False)
        assert fake_beckhoff.user_setpoint.get() == dest
        fake_beckhoff.motor_done_move.sim_put(0)
        fake_beckhoff.user_readback.sim_put(dest)
        fake_beckhoff.plc.status.sim_put(error)
        fake_beckhoff.plc.err_bool.sim_put(bool(error))
        fake_beckhoff.plc.err_code.sim_put(code)
        fake_beckhoff.motor_done_move.sim_put(1)
        return status

    # Known starting configuration
    fake_beckhoff.user_readback.sim_put(0)
    fake_beckhoff.user_setpoint.sim_put(0)
    fake_beckhoff.plc.status.sim_put("")
    fake_beckhoff.plc.err_code.sim_put(0)
    fake_beckhoff.motor_done_move.sim_put(1)
    fake_beckhoff.direction_of_travel.sim_put(0)
    fake_beckhoff.low_limit_switch.sim_put(0)
    fake_beckhoff.high_limit_switch.sim_put(0)
    fake_beckhoff.user_readback.alarm_severity = AlarmSeverity.NO_ALARM
    fake_beckhoff.user_readback.alarm_status = AlarmStatus.NO_ALARM

    # No error normal case
    status = sim_move(dest=1)
    status.wait(timeout=1)

    # No error from cases that would be error in EpicsMotor
    # Limit switch case
    fake_beckhoff.low_limit_switch.sim_put(1)
    status = sim_move(dest=-2)
    status.wait(timeout=1)
    fake_beckhoff.low_limit_switch.sim_put(0)
    # Alarm severity case
    fake_beckhoff.user_readback.alarm_severity = AlarmSeverity.MAJOR
    status = sim_move(dest=3)
    status.wait(timeout=1)
    fake_beckhoff.user_readback.alarm_severity = AlarmSeverity.NO_ALARM

    # Yes error, message preserved
    msg = 'test_error'
    status = sim_move(dest=4, error=msg)
    with pytest.raises(RuntimeError):
        status.wait(timeout=1)
    status_msg = status.exception().args[0]
    assert status_msg == msg

    # Yes error, message and error code preserved
    code = 17056  # Real error code 0x42a0
    status = sim_move(dest=5, error=msg, code=code)
    with pytest.raises(RuntimeError):
        status.wait(timeout=1)
    status_msg = status.exception().args[0]
    assert status_msg in status_msg
    assert hex(code) in status_msg


def test_motor_factory():
    m = Motor('TST:MY:MMS:01', name='test_motor')
    assert isinstance(m, IMS)
    m = Motor('TST:RANDOM:MTR:01', name='test_motor')
    assert isinstance(m, EpicsMotor)


def test_fake_offset_ims(fake_offset_ims):
    off_ims = fake_offset_ims
    # with motor position at 1
    logger.debug('Motor position: %d', off_ims.motor.position)
    logger.debug('User Offset: %d', off_ims.user_offset.get())
    # set offset to 3
    off_ims.user_offset.sim_put(3)
    # pseudo_motor pos => real_pos.motor - self.user_offset.get()
    # pseudo_motor = 1 + -3 = -2
    assert off_ims.pseudo_motor.position == -2

    # set current position to 5
    off_ims.set_current_position(5)
    # new_offset = position - self.position[0]
    # new_offset = 5 - 1 => 4
    logger.debug('New Offset: %d', off_ims.user_offset.get())
    assert off_ims.user_offset.get() == 4
    logger.debug('Motor position %d', off_ims.motor.position)
    # if new offset 4, motor pos == 1
    # pseudo pos = real_pos.motor - self.user_offset.get()
    # 1 - (4) = -3
    assert off_ims.pseudo_motor.position == -3

    # test moving
    off_ims.move(7, wait=False)
    # motor pos =  pseudo_pos.pseudo_motor + self.user_offset.get()
    # 7 + (4) = 11
    assert off_ims.motor.user_setpoint.get() == 11
    # the actuall motor has not move technically, so to trully test the
    # pseudo motor here, we should put the value of motor at 11:
    off_ims.motor.user_readback.sim_put(11)
    # pseudo pos == real_pos.motor - self.user_offset.get()
    # 11 - 4 = 7
    assert off_ims.pseudo_motor.position == 7

    off_ims.motor.user_readback.sim_put(-6)
    # pseudo pos == real_pos.motor - self.user_offset.get()
    # -6 - 4 = -10
    assert off_ims.pseudo_motor.position == -10


def test_offset_ims_with_preset(fake_offset_ims_with_preset):
    off_ims = fake_offset_ims_with_preset
    # set current position to 5
    off_ims.set_current_position(5)
    # new_offset = position - self.position[0]
    # new_offset = 5 - 1 => 4
    logger.debug('New Offset: %d', off_ims.user_offset.get())
    assert off_ims.user_offset.get() == 4
    # because use_ims_preset == True we should have the _SET pv with same value
    assert off_ims.offset_set_pv.get() == 4
    logger.debug('Motor position %d', off_ims.motor.position)
    # if new offset 4, motor pos == 1
    # pseudo pos = real_pos.motor - self.user_offset.get()
    # 1 - (4) = -3
    assert off_ims.pseudo_motor.position == -3


def test_motion_error_filter(fake_epics_motor, caplog):
    # Quick utilities for changing our state
    def sim_do_move(mot):
        mot.move(mot.position + 1, wait=False)
        sim_is_moving(mot)

    def sim_is_moving(mot):
        pos = mot.user_readback.get()
        if mot.user_setpoint.get() == pos:
            mot.user_setpoint.sim_put(pos + 1)
        mot.motor_is_moving.sim_put(1)
        mot.motor_done_move.sim_put(0)

    def sim_done(mot):
        mot.user_readback.sim_put(mot.user_setpoint.get())
        mot.motor_is_moving.sim_put(0)
        mot.motor_done_move.sim_put(1)

    def generate_test_logs(mot):
        num = 0
        num += generate_filtered_logs(mot)
        num += generate_unfiltered_logs(mot)
        return num

    def generate_filtered_logs(mot):
        mot.log.warning('fake log alarm warning')
        mot.log.error('fake log alarm error')
        return 2

    def generate_unfiltered_logs(mot):
        mot.log.warning('fake log warning')
        mot.log.error('fake log error')
        return 2

    def get_logs():
        return list(
            tup for tup in caplog.record_tuples if tup[0] == 'ophyd.objects'
        )

    def assert_real_test(mot):
        # Cause a move and check how many logs at end
        sim_do_move(mot)
        caplog.clear()
        sim_done(mot)
        unfiltered = get_logs()
        # See a move and check how many logs at end
        sim_is_moving(mot)
        caplog.clear()
        sim_done(mot)
        filtered = get_logs()
        msg = "No logs filtered in the observed move."
        assert len(unfiltered) > len(filtered), msg

    # Initialize the alarm status/severity attributes
    fake_epics_motor.user_readback.alarm_status = AlarmStatus.NO_ALARM
    fake_epics_motor.user_readback.alarm_severity = AlarmSeverity.NO_ALARM
    # We expect alarm logs to be filtered outside of moves
    # Make sure the normal mechanisms work: all logs happen during our moves
    sim_do_move(fake_epics_motor)
    caplog.clear()
    count = generate_test_logs(fake_epics_motor)
    normal_logs = get_logs()
    assert len(normal_logs) == count, "Did not see all the logs"
    # Make sure only the unfiltered logs happen between moves
    sim_done(fake_epics_motor)
    caplog.clear()
    generate_filtered_logs(fake_epics_motor)
    count = generate_unfiltered_logs(fake_epics_motor)
    filtered_logs = get_logs()
    assert len(filtered_logs) == count, "Did not filter the logs correctly."

    # Now that the baseline works, examine the full codepaths
    # First, try for an accepted alarm state
    fake_epics_motor.user_readback.alarm_status = AlarmStatus.STATE
    fake_epics_motor.user_readback.alarm_severity = AlarmSeverity.MINOR
    fake_epics_motor.tolerated_alarm = AlarmSeverity.MINOR
    assert_real_test(fake_epics_motor)

    # Second, try for an unaccepted alarm state
    fake_epics_motor.user_readback.alarm_severity = AlarmSeverity.MAJOR
    assert_real_test(fake_epics_motor)


@pytest.mark.parametrize("cls", [PCDSMotorBase, IMS, Newport, MMC100,
                                 PMC100, BeckhoffAxis, EpicsMotor])
@pytest.mark.timeout(5)
def test_disconnected_motors(cls):
    cls('MOTOR', name='motor')


@pytest.mark.parametrize("cls", [OffsetMotor, OffsetIMSWithPreset])
@pytest.mark.timeout(5)
def test_disconnected_offset_motors(cls):
    cls('MOTOR', motor_prefix='MOTOR:PREFIX', name='motor')
