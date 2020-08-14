import logging

import numpy as np
import pytest

from conftest import MODULE_PATH
from ophyd.device import Component as Cpt
from ophyd.positioner import SoftPositioner
from pcdsdevices.lxe import LaserEnergyPlotContext, LaserEnergyPositioner
from pcdsdevices.pseudopos import (DelayBase, LookupTablePositioner,
                                   PseudoSingleInterface, SimDelayStage,
                                   SyncAxesBase)

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


def test_subcls_warning():
    logger.debug('test_subcls_warning')
    with pytest.raises(TypeError):
        SyncAxesBase('prefix', name='name')
    with pytest.raises(TypeError):
        DelayBase('prefix', name='name')


def test_lut_positioner():
    class MyLUTPositioner(LookupTablePositioner):
        pseudo = Cpt(PseudoSingleInterface)
        real = Cpt(SoftPositioner)

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
