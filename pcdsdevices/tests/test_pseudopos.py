import logging

import numpy as np
import pytest
from ophyd.device import Component as Cpt
from ophyd.positioner import SoftPositioner

from ..pseudopos import (DelayBase, LookupTablePositioner, OffsetMotorBase,
                         PseudoSingleInterface, SimDelayStage, SyncAxesBase,
                         SyncAxis, SyncAxisOffsetMode)
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


def test_lut_positioner():
    logger.debug('test_lut_positioner')

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
