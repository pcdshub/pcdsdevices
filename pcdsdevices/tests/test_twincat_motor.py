import logging

import pytest
from ophyd.sim import make_fake_device
from ophyd.utils.epics_pvs import AlarmSeverity, AlarmStatus

from ..twincat_motor import TwinCATAxis, TwinCATAxisEPS, TwinCATMotorInterface

TWINCAT_DEVICES = [TwinCATMotorInterface, TwinCATAxis, TwinCATAxisEPS]

logger = logging.getLogger(__name__)


def fake_class_setup(cls):
    FakeClass = make_fake_device(cls)
    for name, cpt in FakeClass._sig_attrs.items():
        source_cpt = getattr(FakeClass.mro()[1], name)
        cpt._subscriptions.update(source_cpt._subscriptions)
    return FakeClass


def motor_setup(motor):
    motor.low_limit_travel.sim_put(-100)
    motor.high_limit_travel.sim_put(100)
    motor.velocity.sim_put(10)
    if hasattr(motor, "power_is_enabled"):
        motor.power_is_enabled.sim_put(1)
    if hasattr(motor, "negative_motion_is_enabled"):
        motor.negative_motion_is_enabled.sim_put(1)
    if hasattr(motor, "positive_motion_is_enabled"):
        motor.positive_motion_is_enabled.sim_put(1)


def fake_motor(cls, name='test_motor'):
    FakeCls = fake_class_setup(cls)
    motor = FakeCls('TST:MTR', name=name)
    motor_setup(motor)
    return motor


@pytest.fixture(scope='function', params=TWINCAT_DEVICES)
def fake_twincat_motor(request):
    """Fixture for all TwinCAT motor device classes."""
    return fake_motor(request.param, name=f"{request.param.__name__}_{request.node.name}")


def test_twincat_motor_soft_limits(fake_twincat_motor):
    logger.debug('test_twincat_motor_soft_limits')
    m = fake_twincat_motor

    # Check that our limits were set correctly
    assert m.limits == (-100, 100)
    # Check that we can not move past the soft limits
    with pytest.raises(RuntimeError):
        m.move(-150)
    # Try to move to a valid position
    m.move(60, wait=False)
    # move current position to -150
    m.readback.sim_put(-150)
    # Try to set low limit to higher than current position
    with pytest.raises(ValueError):
        # current position: -150
        m.set_low_limit(-101)
    # move current position to 150
    m.readback.sim_put(150)
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
    m.readback.sim_put(-110)
    with pytest.raises(ValueError):
        # current low limit: -100
        # current position: -110
        m.set_high_limit(-105)
    # change the current position to 50
    m.readback.sim_put(50)
    # Try to successfully set the high and low limits:
    # current low limit: -100
    # current high limit: 100
    # current position:  50
    m.set_low_limit(-110)
    m.set_high_limit(110)
    m.check_value(42)
    # Check limits using the .limits property (tuple)
    assert m.limits[0] == -110
    assert m.limits[1] == 110


def test_clearing_limits(fake_twincat_motor):
    m = fake_twincat_motor
    # current limits: -100, 100
    assert m.limits[0] == -100
    assert m.limits[1] == 100
    m.clear_limits()
    assert m.limits[0] == 0
    assert m.limits[1] == 0


def test_twincat_motor_error_clear(fake_twincat_motor):
    m = fake_twincat_motor
    if not isinstance(m, TwinCATAxis):
        return
    m.clear_error()
    assert m.plc.cmd_err_reset.get() == 1
    m.stage()
    m.unstage()


def test_twincat_motor_velo_error(fake_twincat_motor):
    mot = fake_twincat_motor
    if not isinstance(mot, TwinCATAxis):
        pytest.skip("Only applies to TwinCATAxis")
    # Zero velo move fails silently if we don't catch it here
    mot.velocity.sim_put(0)
    low_limit = mot.low_limit_travel.get()
    high_limit = mot.high_limit_travel.get()
    for num in range(low_limit + 1, high_limit):
        with pytest.raises(RuntimeError):
            mot.check_value(num)

    with pytest.raises(RuntimeError):
        mot.move((low_limit + high_limit) / 2, wait=False)


def test_twincat_motor_error_status(fake_twincat_motor):
    # Only run for TwinCATAxis
    if not isinstance(fake_twincat_motor, TwinCATAxis):
        pytest.skip("Only applies to TwinCATAxis")

    # Helper
    def sim_move(dest: float, error: str = '', code: int = 0):
        status = fake_twincat_motor.move(dest, wait=False)
        assert fake_twincat_motor.setpoint.get() == dest
        fake_twincat_motor.done.sim_put(0)
        fake_twincat_motor.readback.sim_put(dest)
        fake_twincat_motor.plc.status.sim_put(error)
        fake_twincat_motor.plc.err_bool.sim_put(bool(error))
        fake_twincat_motor.plc.err_code.sim_put(code)
        fake_twincat_motor.done.sim_put(1)
        return status

    # Known starting configuration
    fake_twincat_motor.readback.sim_put(0)
    fake_twincat_motor.setpoint.sim_put(0)
    fake_twincat_motor.plc.status.sim_put("")
    fake_twincat_motor.plc.err_code.sim_put(0)
    fake_twincat_motor.done.sim_put(1)
    fake_twincat_motor.low_limit_switch.sim_put(0)
    fake_twincat_motor.high_limit_switch.sim_put(0)
    fake_twincat_motor.readback.alarm_severity = AlarmSeverity.NO_ALARM
    fake_twincat_motor.readback.alarm_status = AlarmStatus.NO_ALARM

    # No error normal case
    status = sim_move(dest=1)
    status.wait(timeout=1)

    # Limit switch case
    fake_twincat_motor.low_limit_switch.sim_put(1)
    status = sim_move(dest=-2)
    status.wait(timeout=1)
    fake_twincat_motor.low_limit_switch.sim_put(0)
    # Alarm severity case
    fake_twincat_motor.readback.alarm_severity = AlarmSeverity.MAJOR
    status = sim_move(dest=3)
    status.wait(timeout=1)
    fake_twincat_motor.readback.alarm_severity = AlarmSeverity.NO_ALARM

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


def test_twincat_inheritance():
    motor = TwinCATAxis('TST:AXIS:01', name='axis_motor')
    assert isinstance(motor, TwinCATMotorInterface)

    motor_eps = TwinCATAxisEPS('TST:AXIS:EPS:01', name='axis_motor_eps')
    assert isinstance(motor_eps, TwinCATAxis)


@pytest.mark.parametrize("cls", TWINCAT_DEVICES)
@pytest.mark.timeout(5)
def test_disconnected_motors(cls):
    # Just instantiate; checks no errors even if unconnected
    cls('MOTOR', name='motor')
