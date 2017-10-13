#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import logging
import pytest

try:
    from bluesky.examples import Reader
    from bluesky.plans import trigger_and_read
    has_bluesky = True
except:
    has_bluesky = False

from pcdsdevices.daq import Daq, make_daq_run_engine
from pcdsdevices.sim.daq import SimDaq

logger = logging.getLogger(__name__)


def test_instantiation():
    realdaq = Daq() # NOQA
    fakedaq = SimDaq() # NOQA


@pytest.fixture(scope='function')
def daq():
    return SimDaq()


def test_connect(daq):
    """
    We expect connect to bring the daq from a disconnected state to a connected
    state.
    """
    logger.debug('test_connect')
    assert not daq.connected
    daq.connect()
    assert daq.connected


def test_disconnect(daq):
    """
    We expect disconnect to bring the daq from a connected state to a
    disconnected state.
    """
    logger.debug('test_disconnect')
    assert not daq.connected
    daq.connect()
    assert daq.connected
    daq.disconnect()
    assert not daq.connected


def test_configure(daq):
    """
    We expect the configured attribute to be correct.
    We expect a disconnected daq to connect and then configure.
    We expect a configure with no args to pick the defaults.
    We expect to be able to disconnect after a configure.
    We expect a connected daq to be able to configure.
    We expect configure to return both the old and new configurations.
    We expect read_configure to give us the current configuration, including
    default args.
    """
    logger.debug('test_configure')
    assert not daq.connected
    assert not daq.configured
    daq.configure()
    assert daq.read_configuration() == daq.default_config
    assert daq.connected
    assert daq.configured
    daq.disconnect()
    assert not daq.connected
    assert not daq.configured
    daq.connect()
    assert daq.connected
    assert not daq.configured
    configs = [
        dict(events=1000, use_l3t=True),
        dict(events=1000, use_l3t=True, record=True),
        dict(duration=10, controls=[]),
    ]
    prev_config = daq.read_configuration()
    for config in configs:
        old, new = daq.configure(**config)
        assert old == prev_config
        assert daq.read_configuration() == new
        for key, value in config.items():
            assert new[key] == value
        prev_config = daq.read_configuration()


@pytest.mark.timeout(3)
def test_basic_run(daq):
    """
    We expect a begin without a configure to automatically configure
    We expect the daq to run for the time passed into begin
    We expect that we close the run upon calling end_run
    """
    logger.debug('test_basic_run')
    assert daq.state == 'Disconnected'
    daq.begin(duration=1)
    assert daq.state == 'Running'
    time.sleep(1.3)
    assert daq.state == 'Open'
    daq.end_run()
    assert daq.state == 'Configured'


@pytest.mark.timeout(3)
def test_stop_run(daq):
    """
    We expect the daq to run indefinitely if no time is passed to begin
    We expect that the running stops early if we call stop
    """
    logger.debug('test_stop_run')
    t0 = time.time()
    daq.begin()
    assert daq.state == 'Running'
    time.sleep(1.3)
    assert daq.state == 'Running'
    daq.stop()
    assert daq.state == 'Open'
    less_than_2 = time.time() - t0
    assert less_than_2 < 2


@pytest.mark.timeout(3)
def test_wait_run(daq):
    """
    We expect that wait will block the thread until the daq is no longer
    running
    We expect that a wait when nothing is happening will do nothing
    """
    logger.debug('test_wait_run')
    t0 = time.time()
    daq.wait()
    short_time = time.time() - t0
    assert short_time < 1
    t1 = time.time()
    daq.begin(duration=1)
    daq.wait()
    just_over_1 = time.time() - t1
    assert 1 < just_over_1 < 1.2
    t3 = time.time()
    daq.wait()
    short_time = time.time() - t3
    assert short_time < 1
    daq.end_run()


@pytest.mark.timeout(3)
def test_configured_run(daq):
    """
    We expect begin() to run for the configured time, should a time be
    configured
    """
    logger.debug('test_configured_run')
    daq.configure(duration=1)
    t0 = time.time()
    daq.begin()
    daq.wait()
    just_over_1 = time.time() - t0
    assert 1 < just_over_1 < 1.2
    daq.end_run()


@pytest.mark.timeout(3)
def test_pause_resume(daq):
    """
    We expect pause and resume to work.
    """
    logger.debug('test_pause_resume')
    daq.begin(duration=5)
    assert daq.state == 'Running'
    daq.pause()
    assert daq.state == 'Open'
    daq.resume()
    assert daq.state == 'Running'
    daq.stop()
    assert daq.state == 'Open'
    daq.end_run()
    assert daq.state == 'Configured'


@pytest.mark.skipif(not has_bluesky, reason='Requires Bluesky')
@pytest.mark.timeout(10)
def test_scan(daq):
    """
    We expect that the daq object is usable in a bluesky plan.
    """
    logger.debug('test_scan')
    RE = make_daq_run_engine(daq)

    def plan(reader):
        for i in range(10):
            assert daq.state == 'Running'
            yield from trigger_and_read([reader])
        assert daq.state == 'Running'

    RE(plan(Reader('test', {'zero': lambda: 0})))

    assert daq.state == 'Configured'
