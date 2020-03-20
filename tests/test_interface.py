import fcntl
import logging
import multiprocessing as mp
import os
import signal
import threading
import time

import pytest
from pcdsdevices.interface import (get_engineering_mode, set_engineering_mode,
                                   setup_preset_paths)
from pcdsdevices.sim import FastMotor, SlowMotor

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def slow_motor():
    return SlowMotor(name='sim_slow')


@pytest.fixture(scope='function')
def fast_motor():
    return FastMotor(name='sim_fast')


@pytest.mark.timeout(5)
def test_mv(fast_motor):
    logger.debug('test_mv')
    fast_motor(3, wait=True)
    assert fast_motor.wm() == 3
    fast_motor.mvr(1, wait=True)
    assert fast_motor() == 4


@pytest.mark.timeout(5)
def test_umv(slow_motor):
    logger.debug('test_umv')
    slow_motor._set_position(5)
    slow_motor.umvr(2)
    assert slow_motor.position == 7


def test_camonitor(fast_motor):
    logger.debug('test_camonitor')
    pid = os.getpid()

    def interrupt():
        time.sleep(0.1)
        os.kill(pid, signal.SIGINT)

    threading.Thread(target=interrupt, args=()).start()
    fast_motor.camonitor()


def test_mv_ginput(monkeypatch, fast_motor):
    logger.debug('test_mv_ginput')
    # Importing forces backend selection, so do inside method
    from matplotlib import pyplot as plt  # NOQA

    def fake_plot(*args, **kwargs):
        return

    def fake_ginput(*args, **kwargs):
        return [[12, 24]]

    def fake_get_fignums(*args, **kwargs):
        return local_get_fignums

    monkeypatch.setattr(plt, 'plot', fake_plot)
    monkeypatch.setattr(plt, 'ginput', fake_ginput)
    monkeypatch.setattr(plt, 'get_fignums', fake_get_fignums)

    def inner_test():
        fast_motor.mv_ginput()
        assert fast_motor.position == 12
        fast_motor.move(0)
        assert fast_motor.position == 0

    local_get_fignums = True
    inner_test()

    local_get_fignums = False
    inner_test()

    fast_motor._limits = (-100, 100)
    inner_test()


def test_presets(presets, fast_motor):
    logger.debug('test_presets')

    fast_motor.mv(3, wait=True)
    fast_motor.presets.add_hutch('zero', 0, comment='center')
    fast_motor.presets.add_here_user('sample')
    assert fast_motor.wm_zero() == -3
    assert fast_motor.wm_sample() == 0

    # Clear paths, refresh, should still exist
    old_paths = fast_motor.presets._paths
    setup_preset_paths()
    assert not hasattr(fast_motor, 'wm_zero')
    setup_preset_paths(**old_paths)
    assert fast_motor.wm_zero() == -3
    assert fast_motor.wm_sample() == 0

    fast_motor.mv_zero(wait=True)
    fast_motor.mvr(1, wait=True)
    assert fast_motor.wm_zero() == -1
    assert fast_motor.wm() == 1

    # Sleep for one so we don't override old history
    time.sleep(1)
    fast_motor.presets.positions.zero.update_pos(comment='hats')
    assert fast_motor.wm_zero() == 0
    assert fast_motor.presets.positions.zero.pos == 1

    assert len(fast_motor.presets.positions.zero.history) == 2
    assert len(fast_motor.presets.positions.sample.history) == 1

    repr(fast_motor.presets.positions.zero)
    fast_motor.presets.positions.zero.deactivate()

    with pytest.raises(AttributeError):
        fast_motor.wm_zero()

    with pytest.raises(AttributeError):
        fast_motor.presets.positions.zero

    fast_motor.umv_sample()
    assert fast_motor.wm() == 3

    fast_motor.presets.positions.sample.update_comment('hello there')
    assert len(fast_motor.presets.positions.sample.history) == 2

    def block_file(path, lock):
        with open(path, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            lock.acquire()
            fcntl.flock(f, fcntl.LOCK_UN)

    path = fast_motor.presets.positions.sample.path
    lock = mp.Lock()
    with lock:
        proc = mp.Process(target=block_file, args=(path, lock))
        proc.start()
        time.sleep(0.2)

        assert fast_motor.presets.positions.sample.pos == 3
        fast_motor.presets.positions.sample.update_pos(2)
        assert not hasattr(fast_motor, 'wm_sample')
        fast_motor.presets.sync()
        assert not hasattr(fast_motor, 'mv_sample')

    proc.join()

    fast_motor.presets.sync()
    assert hasattr(fast_motor, 'mv_sample')


def test_presets_type(presets, fast_motor):
    logger.debug('test_presets_type')
    # Mess up the input types, fail before opening the file

    with pytest.raises(TypeError):
        fast_motor.presets.add_here_user(123)
    with pytest.raises(TypeError):
        fast_motor.presets.add_user(234234, 'cats')


def test_engineering_mode():
    logger.debug('test_engineering_mode')
    set_engineering_mode(False)
    assert not get_engineering_mode()
    set_engineering_mode(True)
    assert get_engineering_mode()


def test_dir_whitelist_basic(fast_motor):
    logger.debug('test_dir_whitelist_basic')
    set_engineering_mode(False)
    user_dir = dir(fast_motor)
    set_engineering_mode(True)
    eng_dir = dir(fast_motor)
    assert len(eng_dir) > len(user_dir)
