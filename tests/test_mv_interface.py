import time
import threading
import logging

import pytest
from ophyd.positioner import SoftPositioner

from pcdsdevices.mv_interface import FltMvInterface

logger = logging.getLogger(__name__)


class Motor(SoftPositioner, FltMvInterface):
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
