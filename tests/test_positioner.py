import logging

import pytest
from ophyd.utils import StatusTimeoutError

from pcdsdevices.positioner import FuncPositioner
from pcdsdevices.sim import FastMotor, SlowMotor

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def basic():
    pos = FastMotor()
    return FuncPositioner(
        name='basic',
        move=pos.move,
        get_pos=lambda: pos.position,
        update_rate=0.1,
        )


@pytest.fixture(scope='function')
def advanced():
    pos = SlowMotor()
    return FuncPositioner(
        name='advanced',
        move=pos.move,
        get_pos=lambda: pos.position,
        set_pos=pos.set_position,
        done=lambda: not pos.moving,
        check_value=lambda pos: 0,
        limits=(-10, 10),
        update_rate=0.1,
        timeout=5)


def move_and_check(positioner, points):
    for pos in points:
        positioner.move(pos, wait=True)
        assert positioner.position == pos
        assert positioner.notepad_signal.get() == pos


@pytest.mark.timeout(10)
def test_funcpos_basic(basic):
    logger.debug('test_funcpos_basic')
    move_and_check(basic, [1])
    assert 1 in basic.read()[basic.name].values()
    assert basic.name in basic.hints['fields']


@pytest.mark.timeout(60)
def test_funcpos_moves_basic(basic):
    logger.debug('test_funcpos_moves')
    move_and_check(basic, range(10))


@pytest.mark.timeout(60)
def test_funcpos_moves_advanced(advanced):
    logger.debug('test_funcpos_moves_advanced')
    move_and_check(advanced, range(-5, 5))


@pytest.mark.timeout(10)
def test_funcpos_failure_states(advanced):
    logger.debug('test_funcpos_failure_states')
    with pytest.raises(ValueError):
        advanced.move(20)
    advanced.timeout = 0.1
    advanced.set_position(0)
    status = advanced.move(5, wait=False)
    with pytest.raises(StatusTimeoutError):
        status.wait()
    assert not status.success
