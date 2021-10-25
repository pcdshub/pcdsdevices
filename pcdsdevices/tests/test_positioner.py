import logging

import pytest
from ophyd.signal import Signal
from ophyd.utils import StatusTimeoutError

from ..positioner import FuncPositioner
from ..sim import FastMotor, SlowMotor

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def basic():
    pos = Signal(name='pos')
    return FuncPositioner(
        name='basic',
        move=pos.put,
        get_pos=pos.get,
        update_rate=0.1,
        )


@pytest.fixture(scope='function')
def advanced():
    pos = FastMotor()

    fpstate = dict(status=None)

    def move(*args, **kwargs):
        fpstate['status'] = pos.move(*args, **kwargs)

    def done(*args, **kwargs):
        try:
            return fpstate['status'].done
        except KeyError:
            return True

    return FuncPositioner(
        name='advanced',
        move=move,
        get_pos=lambda: pos.position,
        set_pos=pos.set_position,
        stop=lambda: 0,
        done=done,
        check_value=lambda pos: 0,
        limits=(-10, 10),
        update_rate=0.1,
        timeout=5)


@pytest.fixture(scope='function')
def slow():
    pos = SlowMotor()
    return FuncPositioner(
        name='slow',
        move=pos.move,
        get_pos=lambda: pos.position,
        update_rate=0.1,
        timeout=0.1,
        )


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


@pytest.mark.timeout(10)
def test_funcpos_moves_basic(basic):
    logger.debug('test_funcpos_moves')
    move_and_check(basic, range(3))
    basic.stop()


@pytest.mark.timeout(10)
def test_funcpos_advanced(advanced):
    logger.debug('test_funcpos_advanced')
    advanced.set_position(0)
    advanced.stop()
    advanced.check_value(0)


@pytest.mark.timeout(20)
def test_funcpos_moves_advanced(advanced):
    logger.debug('test_funcpos_moves_advanced')
    move_and_check(advanced, range(3))


@pytest.mark.timeout(10)
def test_funcpos_failure_states(advanced, slow):
    logger.debug('test_funcpos_failure_states')
    with pytest.raises(ValueError):
        advanced.move(20)
    status = slow.move(5, wait=False)
    with pytest.raises(StatusTimeoutError):
        status.wait()
    assert not status.success
    with pytest.raises(ValueError):
        FuncPositioner(name='name', move=lambda: 0, get_pos=lambda: 0)
