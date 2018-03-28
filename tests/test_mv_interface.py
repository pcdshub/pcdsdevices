import time
import threading
import os
import shutil
import logging
from pathlib import Path

import pytest
from ophyd.device import Device
from ophyd.positioner import SoftPositioner

from pcdsdevices.mv_interface import FltMvInterface, setup_preset_paths

logger = logging.getLogger(__name__)


class Motor(SoftPositioner, FltMvInterface):
    _name = 'test'

    def __init__(self):
        super().__init__(name='test')
        self._set_position(0)

    def _setup_move(self, position, status):
        def update_thread(positioner, goal):
            positioner._moving = True
            while positioner.position != goal and not self._stop:
                if goal - positioner.position > 1:
                    positioner._set_position(positioner.position + 1)
                elif goal - positioner.position < -1:
                    positioner._set_position(positioner.position - 1)
                else:
                    positioner._set_position(goal)
                    positioner._done_moving()
                    return
                time.sleep(0.1)
            positioner._done_moving(success=False)
        self.stop()
        self._started_moving = True
        self._stop = False
        t = threading.Thread(target=update_thread,
                             args=(self, position))
        t.start()

    def stop(self):
        self._stop = True


class DeviceTest(FltMvInterface, Device):
    pass


@pytest.fixture(scope='function')
def motor():
    return Motor()


@pytest.fixture(scope='function')
def presets():
    folder_obj = Path(__file__).parent / 'test_presets'
    folder = str(folder_obj)
    if folder_obj.exists():
        shutil.rmtree(folder)
    bl = folder + '/beamline'
    user = folder + '/user'
    os.makedirs(bl)
    os.makedirs(user)
    setup_preset_paths(beamline=bl, user=user)
    yield
    setup_preset_paths()
    shutil.rmtree(folder)


@pytest.mark.timeout(5)
def test_mv(motor):
    logger.debug('test_mv')
    motor(3, wait=True)
    assert motor.wm() == 3
    motor.mvr(1, wait=True)
    assert motor() == 4


@pytest.mark.timeout(5)
def test_umv(motor):
    logger.debug('test_umv')
    motor._set_position(5)
    motor.umvr(2)
    assert motor.position == 7


def test_presets_device(presets):
    # Make sure init works with devices, not just toy positioners
    logger.debug('test_presets_device')
    DeviceTest(name='test')


def test_presets(presets, motor):
    logger.debug('test_presets')
    motor.mv(3, wait=True)
    motor.presets.add_beamline('zero', 0, comment='center')
    motor.presets.add_here_user('sample')
    assert motor.wm_zero() == -3
    assert motor.wm_sample() == 0

    # Clear paths, refresh, should still exist
    old_paths = motor.presets._paths
    setup_preset_paths()
    assert not hasattr(motor, 'wm_zero')
    setup_preset_paths(**old_paths)
    assert motor.wm_zero() == -3
    assert motor.wm_sample() == 0

    motor.mv_zero(wait=True)
    motor.mvr(1, wait=True)
    assert motor.wm_zero() == -1
    assert motor.wm() == 1
    assert motor.presets.positions.zero.comment == 'center'

    # Sleep for one so we don't override old history
    time.sleep(1)
    motor.presets.positions.zero.update_pos()
    assert motor.wm_zero() == 0
    assert motor.presets.positions.zero.pos == 1

    motor.presets.positions.zero.update_comment('uno')
    assert motor.presets.positions.zero.comment == 'uno'
    assert motor.presets.positions.sample.comment is None
    assert len(motor.presets.positions.zero.history) == 2
    assert len(motor.presets.positions.sample.history) == 1

    repr(motor.presets.positions.zero)
    motor.presets.positions.zero.deactivate()

    with pytest.raises(AttributeError):
        motor.wm_zero()

    with pytest.raises(AttributeError):
        motor.presets.positions.zero

    motor.umv_sample()
    assert motor.wm() == 3
