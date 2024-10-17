import logging
import time
from typing import Any

import numpy as np
import pytest
from ophyd.device import Component as Cpt
from ophyd.positioner import SoftPositioner
from ophyd.sim import make_fake_device

from ..pseudopos import (DelayBase, LookupTablePositioner, OffsetMotorBase,
                         PseudoSingleInterface, SimDelayStage, SyncAxesBase,
                         SyncAxis, SyncAxisOffsetMode, is_strictly_increasing)
from ..sim import FastMotor

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


class SyncAxisDefault(SyncAxis):
    one = Cpt(FastMotor)
    two = Cpt(FastMotor)


class SyncAxisAuto(SyncAxis):
    one = Cpt(FastMotor, init_pos=0)
    two = Cpt(FastMotor, init_pos=2)

    offset_mode = SyncAxisOffsetMode.AUTO_FIXED


class SyncAxisCrazy(SyncAxis):
    one = Cpt(FastMotor)
    two = Cpt(FastMotor)
    three = Cpt(FastMotor)

    offsets = {'three': 3}
    scales = {'two': -2, 'three': 3}
    fix_sync_keep_still = 'two'
    sync_limits = (-10, 10)


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


def test_sync_axis_default():
    logger.debug('test_sync_axis_default')
    sync = SyncAxisDefault('DEFAULT', name='sync_default')
    sync.move(5, wait=True)
    assert sync.one.position == 5
    assert sync.two.position == 5
    assert sync.is_synced()
    sync.one.move(0)
    assert not sync.is_synced()
    assert 'fix_sync' in sync.format_status_info(sync.status_info())


def test_sync_axis_auto():
    logger.debug('test_sync_axis_auto')
    sync = SyncAxisAuto('AUTO', name='sync_auto')
    sync.move(5)
    assert sync.one.position == 5
    assert sync.two.position == 7


def test_sync_axis_crazy():
    logger.debug('test_sync_axis_crazy')
    sync = SyncAxisCrazy('CRAZY', name='sync_crazy')
    sync.move(5)
    assert sync.is_synced()
    assert sync.one.position == 5
    assert sync.two.position == -10
    assert sync.three.position == 18
    assert sync.position.sync == 5
    with pytest.raises(Exception):
        sync.move(20)


def test_sync_axis_class_checks():
    logger.debug('test_sync_axis_class_checks')

    class BadSync(SyncAxisDefault):
        def __init__(self):
            super().__init__('Bad', name='bad')

    # Original
    BadSync()
    # Bad offset_mode
    BadSync.offset_mode = 'potatoes'
    with pytest.raises(ValueError):
        BadSync()
    BadSync.offset_mode = SyncAxisOffsetMode.STATIC_FIXED
    # Bad offsets
    BadSync.offsets = {'seven_billion': 3}
    with pytest.raises(ValueError):
        BadSync()
    BadSync.offsets = None
    # Bad scales
    BadSync.scales = {'longcat': 100000000}
    with pytest.raises(ValueError):
        BadSync()
    BadSync.scales = None
    # Bad fix_sync_keep_still
    BadSync.fix_sync_keep_still = 'zoomer'
    with pytest.raises(ValueError):
        BadSync()
    BadSync.fix_sync_keep_still = None


def test_delay_basic():
    logger.debug('test_delay_basic')
    stage_s = SimDelayStage('prefix', name='name', egu='s', n_bounces=2)
    stage_ns = SimDelayStage('prefix', name='name', egu='ns', n_bounces=2)
    stage_inv = SimDelayStage('prefix', name='name', egu='s', n_bounces=2,
                              invert=True)
    approx_c = 3e8
    stage_s.move(1e-9)
    stage_ns.move(1)
    stage_inv.move(-1e-9)
    for pos in (stage_s.motor.position, stage_ns.motor.position,
                stage_inv.motor.position):
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
    with pytest.raises(TypeError):
        OffsetMotorBase('prefix', name='name')


@pytest.mark.parametrize(
    "real_sign,pseudo_sign",
    (
        (1, 1),
        (1, -1),
        (-1, 1),
        (-1, -1),
    )
)
def test_lut_positioner(real_sign: bool, pseudo_sign: bool):
    logger.debug('test_lut_positioner_normal')
    rs = real_sign
    ps = pseudo_sign

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

    signs = np.asarray([[rs, ps]] * 8)
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
    ) * signs
    column_names = ['real', 'pseudo']
    lut = MyLUTPositioner('', table=table, column_names=column_names,
                          name='lut')

    np.testing.assert_allclose(lut.forward(60 * ps)[0], 2 * rs)
    np.testing.assert_allclose(lut.inverse(7 * rs)[0], 200 * ps)
    np.testing.assert_allclose(lut.inverse(1.5 * rs)[0], 55 * ps)

    lut.move(100 * ps, wait=True)
    np.testing.assert_allclose(lut.pseudo.position, 100 * ps)
    np.testing.assert_allclose(lut.real.position, 6 * rs)

    assert lut.real.limits == tuple(sorted([0 * rs, 9 * rs]))
    assert lut.pseudo.limits == tuple(sorted([40 * ps, 400 * ps]))


@pytest.mark.parametrize(
    "input,expected",
    (
        (np.asarray((0, 1, 2, 3, 4, 5)), True),
        (np.asarray((0, 1, 2, 3, 4, 4)), False),
        (np.asarray((0, -1, -2, -3, -4, -5)), False),
        (np.asarray((0, 2, 4, -3, 5, 10)), False),
    ),
)
def test_increasing_helper(input: np.ndarray, expected: bool):
    logger.debug("test_increasing_helper")
    assert is_strictly_increasing(input) == expected


FakeDelayBase = make_fake_device(DelayBase)


class FakeDelay(FakeDelayBase):
    motor = Cpt(FastMotor, egu='mm')


def link_two_signals(signal1, signal2):
    def put_to_1(value, old_value, **kwargs):
        if value != old_value:
            signal1.put(value)

    def put_to_2(value, old_value, **kwargs):
        if value != old_value:
            signal2.put(value)

    signal1.subscribe(put_to_2)
    signal2.subscribe(put_to_1)


@pytest.fixture(scope='function')
def linked_delays():
    delay_one = FakeDelay('SIM', name='delay_one', n_bounces=1)
    delay_two = FakeDelay('SIM', name='delay_two', n_bounces=2)
    link_two_signals(
        delay_one.delay.notepad_readback,
        delay_two.delay.notepad_readback,
    )
    link_two_signals(
        delay_one.delay.notepad_setpoint,
        delay_two.delay.notepad_setpoint,
    )
    delay_one._my_move_timeout = 0.4
    delay_two._my_move_timeout = 0.4
    return delay_one, delay_two


def wait_for(
    obj: Any,
    attr: str,
    value: Any,
    timeout: float = 1,
    dt: float = 0.1,
):
    start_time = time.monotonic()
    while time.monotonic() - start_time > timeout:
        if getattr(obj, attr) == value:
            return
        time.sleep(dt)
    assert getattr(obj, attr) == value


def test_implicit_mutex(linked_delays: tuple[FakeDelay, FakeDelay]):
    # Previous bug: two delays could fight over control of ophyd_readback
    delay_one, delay_two = linked_delays

    def assert_no_updates():
        value1 = delay_one.delay.notepad_readback.get()
        value2 = delay_two.delay.notepad_readback.get()
        if not delay_one._my_move:
            delay_one._update_position()
        if not delay_two._my_move:
            delay_two._update_position()
        assert delay_one.delay.notepad_readback.get() == value1
        assert delay_two.delay.notepad_readback.get() == value2

    # Let's do moves and check _my_move attribute
    assert not delay_one._my_move
    assert not delay_two._my_move
    assert_no_updates()

    # First move: delay_one should immediately grab _my_move
    delay_one.move(1, wait=False)
    assert delay_one._my_move
    assert not delay_two._my_move
    assert_no_updates()

    # Second move: after _my_move_tomeout, delay_one should drop _my_move
    time.sleep(delay_one._my_move_timeout)
    delay_two.move(2, wait=False)
    assert delay_two._my_move
    wait_for(delay_one, '_my_move', False)
    assert_no_updates()

    # Do it again but the other way
    time.sleep(delay_two._my_move_timeout)
    delay_one.move(3, wait=False)
    assert delay_one._my_move
    wait_for(delay_two, '_my_move', False)
    assert_no_updates()
