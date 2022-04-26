import logging

import pytest
from ophyd.sim import make_fake_device

from ..spectrometer import (HXRSpectrometer, Kmono, VonHamos4Crystal,
                            VonHamosFE, VonHamosFER)

logger = logging.getLogger(__name__)


@pytest.mark.timeout(5)
def test_vh_init():
    logger.debug('test_vh_init')
    FakeVH = make_fake_device(VonHamosFE)
    FakeVH(name='test', prefix_focus='zoom', prefix_energy='buzz')
    FakeVH('TST', name='test', prefix_focus='zoom', prefix_energy='buzz')
    FakeVH = make_fake_device(VonHamosFER)
    FakeVH(name='test', prefix_focus='zoom', prefix_energy='buzz',
           prefix_rot='whirl')
    FakeVH('TST', name='test', prefix_focus='zoom', prefix_energy='buzz',
           prefix_rot='whirl')
    FakeVH = make_fake_device(VonHamos4Crystal)
    FakeVH('TST', name='test', prefix_focus='zoom', prefix_energy='buzz')


@pytest.mark.timeout(5)
def test_spectrometer_disconnected():
    logger.debug('test_spectrometer_disconnected')
    Kmono('TST', name='test')
    VonHamosFE('TST2', name='test2', prefix_focus='zoom', prefix_energy='buzz')
    VonHamosFER('TST3', name='test3', prefix_focus='zoom',
                prefix_energy='buzz', prefix_rot='whirl')
    VonHamos4Crystal('TST4', name='test4', prefix_focus='zoom',
                     prefix_energy='buzz')
    HXRSpectrometer('TST5', name='test5')
