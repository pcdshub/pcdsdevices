import logging

import numpy as np
import pytest
from ophyd.device import Component as Cpt
from ophyd.positioner import SoftPositioner
from ophyd.sim import make_fake_device
from ophyd.status import StatusTimeoutError
from ophyd.status import wait as wait_status

from ..lxe import (LaserEnergyPlotContext, LaserEnergyPositioner, LaserTiming,
                   LaserTimingCompensation)
from ..utils import convert_unit
from .conftest import MODULE_PATH

logger = logging.getLogger(__name__)


@pytest.fixture
def lxe_calibration_file():
    return MODULE_PATH / 'xcslt8717_wpcalib_opa'


def test_laser_energy_positioner(monkeypatch, lxe_calibration_file):
    logger.debug('test_laser_energy_positioner')

    class MyLaserEnergyPositioner(LaserEnergyPositioner):
        motor = Cpt(SoftPositioner)

    def no_op(*args, **kwargs):
        ...

    monkeypatch.setattr(LaserEnergyPlotContext, 'plot', no_op)
    monkeypatch.setattr(LaserEnergyPlotContext, 'add_line', no_op)

    lxe = MyLaserEnergyPositioner('', calibration_file=lxe_calibration_file,
                                  name='lxe')
    lxe.move(10)
    lxe.enable_plotting = True
    lxe.move(20)
    lxe.enable_plotting = False
    lxe.move(30)

    with pytest.raises(ValueError):
        # Out-of-range value
        lxe.move(1e9)


def wrap_pv_positioner_move(monkeypatch, pv_positioner):
    """Monkeypatch move method on PV positioner to allow testing."""
    if getattr(pv_positioner.move, '_wrapped', False):
        return

    def move_replacement(position, wait=False, **kwargs):
        st = original_move(position, wait=False, **kwargs)
        # if pv_positioner.done is not None:
        #     pv_positioner.done.sim_put(1 - pv_positioner.done_value)
        #     pv_positioner.done.sim_put(pv_positioner.done_value)
        pv_positioner._done_moving(success=True)
        if wait:
            wait_status(st)
        return st

    move_replacement._wrapped = True
    original_move = pv_positioner.move
    monkeypatch.setattr(pv_positioner, 'move', move_replacement)


def wrap_motor_move(monkeypatch, positioner):
    """Monkeypatch move method on motor to allow testing."""
    if getattr(positioner.move, '_wrapped', False):
        return

    def move_replacement(position, wait=False, **kwargs):
        st = original_move(position, wait=False, **kwargs)
        positioner.user_readback.sim_put(position)
        positioner.motor_done_move.sim_put(1)
        positioner.motor_is_moving.sim_put(0)
        positioner._done_moving(success=True)
        if wait:
            wait_status(st)
        return st

    move_replacement._wrapped = True
    original_move = positioner.move
    monkeypatch.setattr(positioner, 'move', move_replacement)


@pytest.fixture
def lxt(monkeypatch):
    """LaserTiming pseudopositioner device instance for testing."""
    lxt = make_fake_device(LaserTiming)('prefix', name='lxt')
    lxt._fs_tgt_time.sim_set_limits(lxt.limits)
    lxt._fs_tgt_time.sim_put(0)
    wrap_pv_positioner_move(monkeypatch, lxt)
    return lxt


@pytest.mark.xfail
def test_lasertiming_dmov_pass(lxt):
    logger.debug('test_lasertiming_dmov')
    # Ensure the wrapper and pv_positioner done checking are working
    lxt.mv(1e-6, wait=True, timeout=1)


def test_lasertiming_dmov_fail():
    logger.debug('test_lasertiming_dmov_fail')
    FakeLaserTiming = make_fake_device(LaserTiming)
    lxt = FakeLaserTiming('FAKE:VIT', name='fstiming')
    # The move should timeout if the DMOV signal is never put to
    with pytest.raises(StatusTimeoutError):
        lxt.mv(1e-6, wait=True, timeout=1)


def test_laser_timing_motion(lxt):
    logger.debug('test_laser_timing_motion')
    # A basic dependency sanity check...
    np.testing.assert_allclose(convert_unit(1, 's', 'ns'), 1e9)

    for pos in range(1, 3):
        pos *= 1e-6
        lxt.move(pos).wait(1)
        np.testing.assert_allclose(lxt.position, pos)
        np.testing.assert_allclose(-lxt._fs_tgt_time.get(),
                                   convert_unit(pos, 's', 'ns'))

    # Note that the offset adjusts the limits dynamically
    for pos, offset in [(1, 1), (3, 2), (2, -1)]:
        pos *= 1e-6
        offset *= 1e-8

        lxt.user_offset.put(offset)
        assert lxt.user_offset.get() == offset
        assert lxt.setpoint.user_offset == offset

        # Test the forward/inverse offset calculations directly:
        np.testing.assert_allclose(
            lxt.setpoint.forward(pos),
            convert_unit(-(pos - offset), 's', 'ns')
        )
        np.testing.assert_allclose(
            lxt.setpoint.inverse(convert_unit(-(pos - offset), 's', 'ns')),
            pos,
        )

        # And indirectly through moves:
        lxt.move(pos).wait(1)
        np.testing.assert_allclose(lxt.position, pos)
        np.testing.assert_allclose(-lxt._fs_tgt_time.get(),
                                   convert_unit(pos - offset, 's', 'ns'))

    # Ensure we have the expected keys based on kind:
    assert 'lxt_user_offset' in lxt.read()
    assert 'lxt_setpoint' in lxt.read()


def test_laser_timing_delay(lxt):
    """
    Check basic moves are getting to the fs_tgt_time signal.

    That signal's value is off by 10e9 for the ns to s conversion
    and negative due to the convention that positive lxt means earlier laser.
    """

    logger.debug('test_laser_timing_delay')
    assert lxt.wm() == 0
    assert lxt._fs_tgt_time.get() == -0
    lxt.mv(1e-6)
    assert lxt.wm() == 1e-6
    assert lxt._fs_tgt_time.get() == pytest.approx(-1000)
    lxt.mv(-5e-6)
    assert lxt.wm() == -5e-6
    assert lxt._fs_tgt_time.get() == pytest.approx(5000)


def test_laser_timing_limits(lxt):
    logger.debug('test_laser_timing_limits')
    assert lxt.limits == (-10e-6, 10e-6)

    with pytest.raises(ValueError):
        lxt.mv(11e-6)
    with pytest.raises(ValueError):
        lxt.mv(-11e-6)

    with pytest.raises(TypeError):
        lxt.limits = 1
    lxt.limits = (-1e-9, 10e-9)

    with pytest.raises(ValueError):
        lxt.mv(-1.1e-9)
    with pytest.raises(ValueError):
        lxt.mv(11e-9)
    lxt.mv(1e-9)


def test_laser_timing_offset(lxt):
    logger.debug('test_laser_timing_offset')
    print('Dial position is', lxt.position)
    # lxt.limits = (1e-10, 1e-3)
    initial_limits = lxt.limits
    for pos in [1.0e-6, 2.0e-6, 8.0e-4]:
        print('Setting the current position to', pos)
        print('Limits were', lxt.limits)
        lxt.set_current_position(pos)
        print('New offset is', lxt.user_offset.get())
        np.testing.assert_allclose(lxt.position, pos)
        print('New position confirmed')
        print('Adjusted limits are', lxt.limits)
        np.testing.assert_allclose(
            lxt.limits,
            (pos + initial_limits[0],
             pos + initial_limits[1])
        )


def test_laser_timing_no_egu():
    logger.debug('test_laser_timing_no_egu')
    # Should raise ValueError if egu is unrecognized
    with pytest.raises(ValueError):
        LaserTiming('', egu='foobar', name='lxt')


def test_laser_timing_notepad(lxt):
    logger.debug('test_laser_timing_notepad')
    assert lxt.notepad_setpoint.get() == 0
    assert lxt.notepad_readback.get() == 0

    lxt.mv(5e-6)
    assert lxt.notepad_setpoint.get() == 5e-6
    assert lxt.notepad_readback.get() == 0

    def complete_move(*args, **kwargs):
        lxt.done.put(0)
        lxt.done.put(1)
    lxt._fs_tgt_time.subscribe(complete_move, run=False)
    lxt.mv(5e-6)
    assert lxt.notepad_setpoint.get() == 5e-6
    assert lxt.notepad_readback.get() == 5e-6


@pytest.fixture
def lxt_ttc(monkeypatch):
    """LaserTimingCompensation pseudopositioner device instance for testing."""
    lxt_ttc = make_fake_device(LaserTimingCompensation)(
        '',
        delay_prefix='DELAY:',
        laser_prefix='LASER:',
        name='lxt_ttc')

    lxt_ttc.laser._fs_tgt_time.sim_set_limits((0, 4e9))
    lxt_ttc.laser._fs_tgt_time.sim_put(0)
    lxt_ttc.delay.motor.motor_egu.sim_put('mm')
    lxt_ttc.delay.motor.user_readback.sim_put(0)
    lxt_ttc.delay.motor.user_setpoint.sim_set_limits((-1e12, 1e12))
    lxt_ttc.delay.motor.motor_spg.sim_put('Go')
    wrap_pv_positioner_move(monkeypatch, lxt_ttc.laser)
    wrap_motor_move(monkeypatch, lxt_ttc.delay.motor)
    return lxt_ttc


def test_laser_timing_compensation(lxt_ttc):
    logger.debug('test_laser_timing_compensation')

    pos = 1.0e-6
    lxt_ttc.move(pos).wait(timeout=2)

    assert lxt_ttc.position[0] == pos
    assert lxt_ttc.delay.position[0] == pos
    np.testing.assert_allclose(lxt_ttc.laser.position, pos)

    milliseconds_to_mm_values = [
        # Delay motor is inverted:
        -0.0,
        -149896.229,
        -299792.458,
        -449688.68700000003,
        -599584.916,
    ]

    mm_to_seconds_values = [
        -0.0,
        -6.671281903963041e-07,
        -1.3342563807926082e-06,
        -2.001384571188912e-06,
        -2.6685127615852163e-06,
    ]

    np.testing.assert_allclose(
        [lxt_ttc.delay.forward(i * 1e-6).motor
         for i in range(len(milliseconds_to_mm_values))],
        milliseconds_to_mm_values,
    )

    np.testing.assert_allclose(
        [lxt_ttc.delay.inverse(i * 1e5).delay
         for i in range(len(mm_to_seconds_values))],
        mm_to_seconds_values,
    )


@pytest.mark.timeout(5)
def test_lxe_disconnected(lxe_calibration_file):
    logger.debug('test_lxe_disconnected')
    LaserTiming('TST', name='tst')
    LaserEnergyPositioner('TST2', name='tst2',
                          calibration_file=lxe_calibration_file)
    LaserTimingCompensation('TST3', delay_prefix='TST3:DELAY',
                            laser_prefix='TST3:LASER', name='tst3')
