import time
import threading
import os
import shutil
import logging

import pytest
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


@pytest.fixture(scope='function')
def motor():
    return Motor()


@pytest.fixture(scope='function')
def presets_motor():
    folder = 'test_presets'
    bl = folder + '/beamline'
    user = folder + '/user'
    os.makedirs(bl)
    os.makedirs(user)
    setup_preset_paths(beamline=bl, user=user)
    yield Motor()
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


def test_presets(presets_motor):
    presets_motor.mv(3, wait=True)
    presets_motor.presets.add_beamline('zero', 0, comment='center')
    presets_motor.presets.add_here_user('sample')
    assert presets_motor.wm_zero() == -3
    assert presets_motor.wm_sample() == 0

    presets_motor.mv_zero(wait=True)
    presets_motor.mvr(1, wait=True)
    assert presets_motor.wm_zero() == -1
    assert presets_motor.wm() == 1
    assert presets_motor.presets.positions.zero.comment == 'center'

    presets_motor.presets.positions.zero.update_pos()
    assert presets_motor.wm_zero() == 0
    assert presets_motor.presets.positions.zero.pos == 1

    presets_motor.presets.positions.zero.update_comment('uno')
    assert presets_motor.presets.positions.zero.comment == 'uno'
    assert presets_motor.presets.positions.sample.comment is None
    assert len(presets_motor.presets.positions.zero.history) == 1
    assert presets_motor.presets.positions.sample.history is None

    repr(presets_motor.presets.positions.zero)
    presets_motor.presets.positions.zero.deactivate()

    with pytest.raises(AttributeError):
        presets_motor.wm_zero()

    with pytest.raises(AttributeError):
        presets_motor.presets.positions.zero

    presets_motor.umv_sample()
    assert presets_motor.wm() == 3
