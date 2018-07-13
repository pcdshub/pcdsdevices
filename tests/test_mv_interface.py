import fcntl
import logging
import multiprocessing as mp
import threading
import time
import os
import signal
import shutil
from pathlib import Path

import pytest

from pcdsdevices.mv_interface import setup_preset_paths
from pcdsdevices.sim.motor import SynAxisInterface, SimMotor

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def sim_motor():
    return SimMotor(name='sim')


@pytest.fixture(scope='function')
def syn_axis():
    return SynAxisInterface(name='syn')


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
def test_mv(syn_axis):
    logger.debug('test_mv')
    syn_axis(3, wait=True)
    assert syn_axis.wm() == 3
    syn_axis.mvr(1, wait=True)
    assert syn_axis() == 4


@pytest.mark.timeout(5)
def test_umv(sim_motor):
    logger.debug('test_umv')
    sim_motor._set_position(5)
    sim_motor.umvr(2)
    assert sim_motor.position == 7


def test_camonitor(syn_axis):
    logger.debug('test_camonitor')
    pid = os.getpid()

    def interrupt():
        time.sleep(0.1)
        os.kill(pid, signal.SIGINT)

    threading.Thread(target=interrupt, args=()).start()
    syn_axis.camonitor()


def test_presets(presets, syn_axis):
    logger.debug('test_presets')
    syn_axis.mv(3, wait=True)
    syn_axis.presets.add_beamline('zero', 0, comment='center')
    syn_axis.presets.add_here_user('sample')
    assert syn_axis.wm_zero() == -3
    assert syn_axis.wm_sample() == 0

    # Clear paths, refresh, should still exist
    old_paths = syn_axis.presets._paths
    setup_preset_paths()
    assert not hasattr(syn_axis, 'wm_zero')
    setup_preset_paths(**old_paths)
    assert syn_axis.wm_zero() == -3
    assert syn_axis.wm_sample() == 0

    syn_axis.mv_zero(wait=True)
    syn_axis.mvr(1, wait=True)
    assert syn_axis.wm_zero() == -1
    assert syn_axis.wm() == 1

    # Sleep for one so we don't override old history
    time.sleep(1)
    syn_axis.presets.positions.zero.update_pos(comment='hats')
    assert syn_axis.wm_zero() == 0
    assert syn_axis.presets.positions.zero.pos == 1

    assert len(syn_axis.presets.positions.zero.history) == 2
    assert len(syn_axis.presets.positions.sample.history) == 1

    repr(syn_axis.presets.positions.zero)
    syn_axis.presets.positions.zero.deactivate()

    with pytest.raises(AttributeError):
        syn_axis.wm_zero()

    with pytest.raises(AttributeError):
        syn_axis.presets.positions.zero

    syn_axis.umv_sample()
    assert syn_axis.wm() == 3

    syn_axis.presets.positions.sample.update_comment('hello there')
    assert len(syn_axis.presets.positions.sample.history) == 2

    def block_file(path, lock):
        with open(path, 'r+') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            lock.acquire()
            fcntl.flock(f, fcntl.LOCK_UN)

    path = syn_axis.presets.positions.sample.path
    lock = mp.Lock()
    with lock:
        proc = mp.Process(target=block_file, args=(path, lock))
        proc.start()
        time.sleep(0.2)

        assert syn_axis.presets.positions.sample.pos == 3
        syn_axis.presets.positions.sample.update_pos(2)
        assert not hasattr(syn_axis, 'wm_sample')
        syn_axis.presets.sync()
        assert not hasattr(syn_axis, 'mv_sample')

    proc.join()

    syn_axis.presets.sync()
    assert hasattr(syn_axis, 'mv_sample')


def test_presets_type(presets, syn_axis):
    logger.debug('test_presets_type')
    # Mess up the input types, fail before opening the file

    with pytest.raises(TypeError):
        syn_axis.presets.add_here_user(123)
    with pytest.raises(TypeError):
        syn_axis.presets.add_user(234234, 'cats')
