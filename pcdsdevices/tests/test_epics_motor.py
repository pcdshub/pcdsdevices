import logging

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import close_run, open_run, stage, unstage
from ophyd.device import Component as Cpt
from ophyd.signal import AttributeSignal
from ophyd.sim import make_fake_device
from ophyd.status import MoveStatus
from ophyd.status import wait as status_wait
from ophyd.utils.epics_pvs import AlarmSeverity, AlarmStatus
from ophyd.utils.errors import LimitError

from ..epics_motor import (IMS, MMC100, PMC100, BeckhoffAxis, EpicsMotor,
                           EpicsMotorInterface, Motor, MotorDisabledError,
                           Newport, OffsetIMSWithPreset, OffsetMotor,
                           PCDSMotorBase)
from ..twincat_motor import TwinCATAxis, TwinCATAxisEPS, TwinCATMotorInterface

logger = logging.getLogger(__name__)

TWINCAT_DEVICES = [TwinCATMotorInterface, TwinCATAxis, TwinCATAxisEPS]


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

    if isinstance(motor, TwinCATMotorInterface):
        motor.readback.sim_put(0)
        motor.setpoint.sim_put(0)
        motor.velocity.sim_put(10)
        motor.low_limit_travel.sim_put(-100)
        motor.high_limit_travel.sim_put(100)
        motor.low_limit_enable.sim_put(1)
        motor.high_limit_enable.sim_put(1)
        motor.power_is_enabled.sim_put(1)
        motor.negative_dir_enabled.sim_put(1)
        motor.positive_dir_enabled.sim_put(1)


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
                params=[
                    EpicsMotorInterface, PCDSMotorBase, IMS, Newport,
                    MMC100, PMC100, BeckhoffAxis,
                    TwinCATMotorInterface, TwinCATAxis, TwinCATAxisEPS
                ])
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
def fake_twincat_motor(request):
    """Fixture for all TwinCAT motor device classes."""
    return fake_motor(TwinCATAxis, name=f'mot_{request.node.name}')


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
    """
    Test soft limit handling for both classic EPICS motors and TwinCAT motors.

    - Checks that initial limits are set correctly.
    - Verifies that moves beyond the limits raise the correct error for each motor class.
    - Simulates readback changes and verifies that the device prevents setting invalid limits depending on current position.
    - Ensures setting and checking new, in-range limits works for all classes.
    """
    logger.debug('test_epics_motor_soft_limits')

    m = fake_epics_motor

    # Common way to get and set position for all device types
    readback_signal = getattr(m, 'readback', getattr(m, 'user_readback', None))

    # Access limits as a tuple always
    limits_tuple = getattr(m, 'limits', lambda: (m.get_low_limit(), m.get_high_limit()))
    low_limit = limits_tuple[0]
    high_limit = limits_tuple[1]

    # Initial limits checks
    assert low_limit == -100
    assert high_limit == 100

    # Check cannot move past the soft limits
    with pytest.raises(ValueError):
        m.move(-150)
    m.move(60, wait=False)

    # Move current position to -150
    readback_signal.sim_put(-150)
    with pytest.raises(ValueError):
        m.set_low_limit(-101)

    # Move current position to 150
    readback_signal.sim_put(150)
    with pytest.raises(ValueError):
        m.set_low_limit(120)
    with pytest.raises(ValueError):
        m.set_high_limit(90)

    # Move current position to -110, test high limit below low limit
    readback_signal.sim_put(-110)
    with pytest.raises(ValueError):
        m.set_high_limit(-105)

    # Move back to in-bounds
    readback_signal.sim_put(50)

    # Set both high and low limits successfully and verify
    m.set_low_limit(-110)
    m.set_high_limit(110)
    m.check_value(42)

    # For assertion, if get_low_limit/get_high_limit exist, use them; otherwise, use .limits
    low_after = getattr(m, 'get_low_limit', lambda: m.limits[0])()
    high_after = getattr(m, 'get_high_limit', lambda: m.limits[1])()
    assert low_after == -110
    assert high_after == 110


def test_clearing_limits(fake_epics_motor):
    """
    Test clearing soft limits on both classic Epics motors and TwinCAT motors.

    - Verifies initial limits are as expected.
    - After calling clear_limits(), confirms both limits are set to 0,
      using either the tuple interface (TwinCAT) or getter methods (legacy).
    """
    m = fake_epics_motor
    is_twincat_motor = isinstance(m, TwinCATMotorInterface)

    # Check current limits before clearing
    if is_twincat_motor:
        # TwinCAT Motor: uses .limits tuple
        assert m.limits[0] == -100  # current low limit
        assert m.limits[1] == 100   # current high limit
    else:
        # Legacy motor: uses getter methods
        assert m.get_low_limit() == -100
        assert m.get_high_limit() == 100

    # Clear limits (should set both to zero)
    m.clear_limits()

    if is_twincat_motor:
        # After clearing, both limits should be zero
        assert m.limits[0] == 0
        assert m.limits[1] == 0
    else:
        assert m.get_low_limit() == 0
        assert m.get_high_limit() == 0


@pytest.mark.parametrize("cls", [EpicsMotorInterface, TwinCATMotorInterface])
def test_limits_update_from_epics(cls):
    """
    Test high/low limit updates via PV for EpicsMotorInterface and TwinCATMotorInterface.
    """
    FakeCls = make_fake_device(cls)
    mot = FakeCls('TST:MTR', name=f"{cls.__name__}_limits_update")
    # Standard setup for both
    mot.high_limit_travel.put(100)
    mot.low_limit_travel.put(-100)
    mot.velocity.sim_put(10)

    is_twincat_motor = issubclass(cls, TwinCATMotorInterface)
    exc_type = RuntimeError if is_twincat_motor else LimitError

    for low, high in (
        (-10, 10),
        (-100, 100),
        (0, 100),
        (-100, 0),
    ):
        mot.high_limit_travel.put(high)
        mot.low_limit_travel.put(low)
        assert mot.limits == (low, high)
        for num in range(low + 1, high):
            mot.check_value(num)
        for num in list(range(low - 10, low)) + list(range(high + 1, high + 10)):
            with pytest.raises(exc_type):
                mot.check_value(num)


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


@pytest.mark.parametrize("cls", [BeckhoffAxis, TwinCATAxis])
def test_beckhoff_error_clear(cls):
    FakeCls = make_fake_device(cls)
    m = FakeCls('TST:MTR', name=f"{cls.__name__}_error_clear")
    m.clear_error()
    assert m.plc.cmd_err_reset.get() == 1
    m.stage()
    m.unstage()


@pytest.mark.parametrize("cls", [BeckhoffAxis, TwinCATAxis])
def test_beckhoff_velo_error(cls):
    """
    Test that velocity=0 moves always raise RuntimeError for Beckhoff/TwinCAT axes.
    """
    FakeCls = make_fake_device(cls)
    mot = FakeCls('TST:MTR', name=f"{cls.__name__}_velo_error")
    # Zero velo move fails silently if we don't catch it here
    mot.velocity.sim_put(0)
    low_limit = mot.low_limit_travel.get()
    high_limit = mot.high_limit_travel.get()
    for num in range(low_limit + 1, high_limit):
        with pytest.raises(RuntimeError):
            mot.check_value(num)

    with pytest.raises(RuntimeError):
        mot.move((low_limit + high_limit) / 2, wait=False)


@pytest.mark.parametrize("cls", [BeckhoffAxis, TwinCATAxis])
def test_beckhoff_error_status(cls):
    """
    Test error reporting on completed moves for both Beckhoff/TwinCAT axes.
    """
    FakeCls = make_fake_device(cls)
    m = FakeCls('TST:MTR', name=f"{cls.__name__}_error_status")

    user_readback = getattr(m, "user_readback", getattr(m, "readback", None))
    user_setpoint = getattr(m, "user_setpoint", getattr(m, "setpoint", None))
    motor_done_move = getattr(m, "motor_done_move", getattr(m, "done", None))

    def sim_move(dest: float, error: str = '', code: int = 0) -> MoveStatus:
        status = m.move(dest, wait=False)
        assert user_setpoint.get() == dest
        motor_done_move.sim_put(0)
        user_readback.sim_put(dest)
        m.plc.status.sim_put(error)
        m.plc.err_bool.sim_put(bool(error))
        m.plc.err_code.sim_put(code)
        motor_done_move.sim_put(1)
        return status

    # Known starting configuration
    user_readback.sim_put(0)
    user_setpoint.sim_put(0)
    m.plc.status.sim_put("")
    m.plc.err_code.sim_put(0)
    motor_done_move.sim_put(1)
    m.velocity.sim_put(10)
    # Only setup direction_of_travel if it exists
    if hasattr(m, "direction_of_travel") and m.direction_of_travel is not None:
        m.direction_of_travel.sim_put(0)

    m.low_limit_switch.sim_put(0)
    m.high_limit_switch.sim_put(0)
    user_readback.alarm_severity = AlarmSeverity.NO_ALARM
    user_readback.alarm_status = AlarmStatus.NO_ALARM

    # No error, normal case
    status = sim_move(dest=1)
    status.wait(timeout=1)

    # Limit switch case (no error)
    m.low_limit_switch.sim_put(1)
    status = sim_move(dest=-2)
    status.wait(timeout=1)
    m.low_limit_switch.sim_put(0)

    # Alarm severity case (no error)
    user_readback.alarm_severity = AlarmSeverity.MAJOR
    status = sim_move(dest=3)
    status.wait(timeout=1)
    user_readback.alarm_severity = AlarmSeverity.NO_ALARM

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
    assert msg in status_msg
    assert hex(code) in status_msg


def test_motor_factory():
    m = Motor('TST:MY:MMS:01', name='test_motor')
    assert isinstance(m, IMS)
    m = Motor('TST:RANDOM:MTR:01', name='test_motor')
    assert isinstance(m, EpicsMotor)
    m = TwinCATAxis('TST:TWINCAT:MTR:01', name='test_motor')
    assert isinstance(m, TwinCATMotorInterface)


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
    """
    Test that alarm/error log filtering works during/after moves,
    for both legacy Epics and TwinCAT motor devices.
    """

    # Use getattr to support both Epics and TwinCAT attribute names
    readback = getattr(fake_epics_motor, 'user_readback', getattr(fake_epics_motor, 'readback', None))
    setpoint = getattr(fake_epics_motor, 'user_setpoint', getattr(fake_epics_motor, 'setpoint', None))
    motor_is_moving = getattr(fake_epics_motor, 'motor_is_moving')
    motor_done_move = getattr(fake_epics_motor, 'motor_done_move', getattr(fake_epics_motor, 'done', None))

    # Quick utilities for changing our state
    def sim_do_move(mot):
        mot.move(setpoint.get() + 1, wait=False)
        sim_is_moving(mot)

    def sim_is_moving(mot):
        pos = readback.get()
        if setpoint.get() == pos:
            setpoint.sim_put(pos + 1)
        motor_is_moving.sim_put(1)
        motor_done_move.sim_put(0)

    def sim_done(mot):
        readback.sim_put(setpoint.get())
        motor_is_moving.sim_put(0)
        motor_done_move.sim_put(1)

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
        # Only log messages for ophyd.objects (same as before)
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
    readback.alarm_status = AlarmStatus.NO_ALARM
    readback.alarm_severity = AlarmSeverity.NO_ALARM

    # Baseline: all logs happen during moves
    sim_do_move(fake_epics_motor)
    caplog.clear()
    count = generate_test_logs(fake_epics_motor)
    normal_logs = get_logs()
    assert len(normal_logs) == count, "Did not see all the logs"
    # Only the unfiltered logs happen between moves
    sim_done(fake_epics_motor)
    caplog.clear()
    generate_filtered_logs(fake_epics_motor)
    count = generate_unfiltered_logs(fake_epics_motor)
    filtered_logs = get_logs()
    assert len(filtered_logs) == count, "Did not filter the logs correctly."

    # Try for an accepted alarm state
    readback.alarm_status = AlarmStatus.STATE
    readback.alarm_severity = AlarmSeverity.MINOR
    fake_epics_motor.tolerated_alarm = AlarmSeverity.MINOR
    assert_real_test(fake_epics_motor)

    # Try for an unaccepted alarm state
    readback.alarm_severity = AlarmSeverity.MAJOR
    assert_real_test(fake_epics_motor)


@pytest.mark.parametrize("cls", [PCDSMotorBase, IMS, Newport, MMC100,
                                 PMC100, BeckhoffAxis, EpicsMotor, TwinCATAxis])
@pytest.mark.timeout(5)
def test_disconnected_motors(cls):
    cls('MOTOR', name='motor')


@pytest.mark.parametrize("cls", [OffsetMotor, OffsetIMSWithPreset])
@pytest.mark.timeout(5)
def test_disconnected_offset_motors(cls):
    cls('MOTOR', motor_prefix='MOTOR:PREFIX', name='motor')


class LimSetterMotor(fake_class_setup(EpicsMotorInterface)):
    """
    Partially fake motor that is picky about its limits

    Simulates some common motor ioc limit setting constraints
    """
    # Redirect these signals in a way that gives us easy control
    low_limit_travel = Cpt(AttributeSignal, '_lim_low')
    high_limit_travel = Cpt(AttributeSignal, '_lim_high')

    def __init__(self, *args, **kwargs):
        self._sim_limits = [0, 0]
        super().__init__(*args, **kwargs)

    @property
    def _lim_low(self):
        """
        Route low_limit_travel.get to our sim limits
        """
        return self._sim_limits[0]

    @_lim_low.setter
    def _lim_low(self, val):
        """
        Clamp low limit to <= high limit
        """
        if val <= self._sim_limits[1]:
            self._sim_limits[0] = val
        else:
            self._sim_limits[0] = self._sim_limits[1]

    @property
    def _lim_high(self):
        """
        Route high_limit_travel.get to our sim limits
        """
        return self._sim_limits[1]

    @_lim_high.setter
    def _lim_high(self, val):
        """
        Clamp high limit to >= low limit
        """
        if val >= self._sim_limits[0]:
            self._sim_limits[1] = val
        else:
            self._sim_limits[1] = self._sim_limits[0]


def test_limits_setter():
    mot = LimSetterMotor('', name='mot')

    def lims():
        return (mot.low_limit_travel.get(), mot.high_limit_travel.get())

    # Default
    assert lims() == (0, 0)
    # Basic
    mot.limits = (-10, 10)
    assert lims() == (-10, 10)
    # Metacheck of LimSetterMotor
    mot.low_limit_travel.put(30)
    assert lims() == (10, 10)
    mot.high_limit_travel.put(0)
    assert lims() == (10, 10)
    # Swapped + above range
    mot.limits = (-10, 10)
    mot.limits = (40, 20)
    assert lims() == (20, 40)
    # 3 elems
    with pytest.raises(ValueError):
        mot.limits = (20, 30, 40)
    # Below range
    mot.limits = (-100, -50)
    assert lims() == (-100, -50)
    # Same twice
    mot.limits = (90, 90)
    assert lims() == (0, 0)
