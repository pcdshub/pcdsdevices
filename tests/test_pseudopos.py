import logging

import numpy as np
import pytest
from conftest import MODULE_PATH
from ophyd.device import Component as Cpt
from ophyd.positioner import SoftPositioner
from ophyd.sim import make_fake_device
from ophyd.status import wait as wait_status

from pcdsdevices.lxe import (LaserEnergyPlotContext, LaserEnergyPositioner,
                             LaserTiming, LaserTimingCompensation)
from pcdsdevices.pseudopos import (DelayBase, LookupTablePositioner,
                                   PseudoSingleInterface, SimDelayStage,
                                   SyncAxesBase)
from pcdsdevices.utils import convert_unit

logger = logging.getLogger(__name__)


class FiveSyncSoftPositioner(SyncAxesBase):
    one = Cpt(SoftPositioner, init_pos=0)
    two = Cpt(SoftPositioner, init_pos=0)
    three = Cpt(SoftPositioner, init_pos=0)
    four = Cpt(SoftPositioner, init_pos=0)
    five = Cpt(SoftPositioner, init_pos=0)


class MaxTwoSyncSoftPositioner(SyncAxesBase):
    one = Cpt(SoftPositioner, init_pos=1)
    two = Cpt(SoftPositioner, init_pos=5)

    def calc_combined(self, real_position):
        return max(real_position)


@pytest.fixture(scope='function')
def five_axes():
    return FiveSyncSoftPositioner(name='sync', egu='five')


@pytest.fixture(scope='function')
def two_axes():
    return MaxTwoSyncSoftPositioner(name='sync', egu='two')


def test_sync_passthrough(five_axes):
    logger.debug('test_sync_passthrough')
    assert five_axes.name == 'sync'
    assert five_axes.egu == 'five'


def test_sync_basic(five_axes):
    logger.debug('test_sync_basic')
    five_axes.move(5)
    for i, pos in enumerate(five_axes.real_position):
        assert pos == 5
    assert five_axes.pseudo.position == 5


def test_sync_offset(five_axes, two_axes):
    logger.debug('test_sync_offset')
    five_axes.one.move(1)
    five_axes.two.move(2)
    five_axes.three.move(3)
    five_axes.four.move(4)
    five_axes.five.move(5)
    assert five_axes.pseudo.position == 1
    five_axes.move(10)
    assert five_axes.one.position == 10
    assert five_axes.two.position == 11
    assert five_axes.three.position == 12
    assert five_axes.four.position == 13
    assert five_axes.five.position == 14

    assert two_axes.pseudo.position == 5


def test_delay_basic():
    stage_s = SimDelayStage('prefix', name='name', egu='s', n_bounces=2)
    stage_ns = SimDelayStage('prefix', name='name', egu='ns', n_bounces=2)
    approx_c = 3e8
    stage_s.move(1e-9)
    stage_ns.move(1)
    for pos in stage_s.motor.position, stage_ns.motor.position:
        assert abs(pos*1e-3 - 1e-9 * approx_c / 2) < 0.01

    stage_s.set_current_position(1.0e-6)
    np.testing.assert_allclose(stage_s.position[0], 1.e-6)
    np.testing.assert_allclose(stage_s.user_offset.get(), 1.e-6 - 1.e-9)


def test_subcls_warning():
    logger.debug('test_subcls_warning')
    with pytest.raises(TypeError):
        SyncAxesBase('prefix', name='name')
    with pytest.raises(TypeError):
        DelayBase('prefix', name='name')


def test_lut_positioner():
    class LimitSettableSoftPositioner(SoftPositioner):
        @property
        def limits(self):
            return self._limits

        @limits.setter
        def limits(self, value):
            self._limits = tuple(value)

    class MyLUTPositioner(LookupTablePositioner):
        pseudo = Cpt(PseudoSingleInterface)
        real = Cpt(LimitSettableSoftPositioner)

    table = np.asarray(
        [[0, 40],
         [1, 50],
         [2, 60],
         [5, 90],
         [6, 100],
         [7, 200],
         [8, 300],
         [9, 400],
         ]
    )
    column_names = ['real', 'pseudo']
    lut = MyLUTPositioner('', table=table, column_names=column_names,
                          name='lut')

    np.testing.assert_allclose(lut.forward(60)[0], 2)
    np.testing.assert_allclose(lut.inverse(7)[0], 200)
    np.testing.assert_allclose(lut.inverse(1.5)[0], 55)

    lut.move(100, wait=True)
    np.testing.assert_allclose(lut.pseudo.position, 100)
    np.testing.assert_allclose(lut.real.position, 6)

    assert lut.real.limits == (0, 9)
    assert lut.pseudo.limits == (40, 400)


@pytest.fixture
def lxe_calibration_file():
    return MODULE_PATH / 'xcslt8717_wpcalib_opa'


def test_laser_energy_positioner(monkeypatch, lxe_calibration_file):
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
    """LaserTiming pseudopositioner device instance"""
    lxt = make_fake_device(LaserTiming)('prefix', name='lxt')
    lxt._fs_tgt_time.sim_set_limits((0, 4e9))
    lxt._fs_tgt_time.sim_put(0)
    wrap_pv_positioner_move(monkeypatch, lxt)
    return lxt


def test_laser_timing_motion(lxt):
    # A basic dependency sanity check...
    np.testing.assert_allclose(convert_unit(1, 's', 'ns'), 1e9)

    for pos in range(1, 3):
        lxt.move(pos).wait(1)
        np.testing.assert_allclose(lxt.position, pos)
        np.testing.assert_allclose(lxt._fs_tgt_time.get(),
                                   convert_unit(pos, 's', 'ns'))

    # Note that the offset adjusts the limits dynamically
    for pos, offset in [(1, 1), (3, 2), (2, -1)]:
        lxt.user_offset.put(offset)
        assert lxt.user_offset.get() == offset
        assert lxt.setpoint.user_offset == offset

        # Test the forward/inverse offset calculations directly:
        np.testing.assert_allclose(
            lxt.setpoint.forward(pos),
            convert_unit(pos - offset, 's', 'ns')
        )
        np.testing.assert_allclose(
            lxt.setpoint.inverse(convert_unit(pos - offset, 's', 'ns')),
            pos,
        )

        # And indirectly through moves:
        lxt.move(pos).wait(1)
        np.testing.assert_allclose(lxt.position, pos)
        np.testing.assert_allclose(lxt._fs_tgt_time.get(),
                                   convert_unit(pos - offset, 's', 'ns'))

    # Ensure we have the expected keys based on kind:
    assert 'lxt_user_offset' in lxt.read_configuration()
    assert 'lxt_setpoint' in lxt.read()


def test_laser_timing_offset(lxt):
    print('Dial position is', lxt.position)
    initial_limits = lxt.limits
    for pos in [1.0, 2.0, -1.0, 8.0]:
        print('Setting the current position to', pos)
        lxt.set_current_position(pos)
        print('New offset is', lxt.user_offset.get())
        np.testing.assert_allclose(lxt.position, pos)
        print('Adjusted limits are', lxt.limits)
        assert lxt.limits == (pos + initial_limits[0], pos + initial_limits[1])


def test_laser_energy_timing_no_egu():
    with pytest.raises(ValueError):
        LaserTiming('', egu='foobar', name='lxt')


@pytest.fixture
def lxt_ttc(monkeypatch):
    """LaserTimingCompensation pseudopositioner device instance"""
    lxt_ttc = make_fake_device(LaserTimingCompensation)(
        '',
        delay_prefix='DELAY:',
        laser_prefix='LASER:',
        name='lxt_ttc')

    lxt_ttc.laser._fs_tgt_time.sim_set_limits((0, 4e9))
    lxt_ttc.laser._fs_tgt_time.sim_put(0)
    lxt_ttc.delay.motor.motor_egu.sim_put('mm')
    lxt_ttc.delay.motor.user_readback.sim_put(0)
    lxt_ttc.delay.motor.user_setpoint.sim_set_limits((0, 1e12))
    lxt_ttc.delay.motor.motor_spg.sim_put('Go')
    wrap_pv_positioner_move(monkeypatch, lxt_ttc.laser)
    wrap_motor_move(monkeypatch, lxt_ttc.delay.motor)
    return lxt_ttc


def test_laser_timing_compensation(lxt_ttc):
    st = lxt_ttc.move(1)
    st.wait(timeout=2)
    assert lxt_ttc.position[0] == 1.0
    assert lxt_ttc.delay.position[0] == 1.0
    np.testing.assert_allclose(lxt_ttc.laser.position, 1.0)

    seconds_to_mm_values = [
        0.0,
        149896229000.0,
        299792458000.0,
        449688687000.0,
        599584916000.0,
    ]

    mm_to_seconds_values = [
        0.0,
        0.06671281903963042,
        0.13342563807926083,
        0.20013845711889122,
        0.26685127615852167,
    ]

    np.testing.assert_allclose(
        [lxt_ttc.delay.forward(i).motor
         for i in range(len(seconds_to_mm_values))],
        seconds_to_mm_values,
    )

    np.testing.assert_allclose(
        [lxt_ttc.delay.inverse(i * 1e10).delay
         for i in range(len(mm_to_seconds_values))],
        mm_to_seconds_values,
    )
