#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import pytest

from bluesky import RunEngine
from bluesky.examples import Reader
from bluesky.plans import (fly_during_decorator, stage_decorator,
                           run_decorator, trigger_and_read)

from pcdsdevices.daq import Daq
from pcdsdevices.sim.daq import SimDaq


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
    assert not daq.connected
    daq.connect()
    assert daq.connected


def test_disconnect(daq):
    """
    We expect disconnect to bring the daq from a connected state to a
    disconnected state.
    """
    assert not daq.connected
    daq.connect()
    assert daq.connected
    daq.disconnect()
    assert not daq.connected


def test_configure(daq):
    """
    We expect the configured attribute to be correct.
    We expect a disconnected daq to connect and then configure.
    We expect to be able to disconnect after a configure.
    We expect a connected daq to be able to configure.
    We expect configure to return both the old and new configurations.
    We expect read_configure to give us the current configuration, including
    default args.
    We expect neglecting to provide both events and duration to raise an error.
    """
    assert not daq.connected
    assert not daq.configured
    daq.configure(events=1000)
    assert daq.read_configuration()['events'] == 1000
    assert daq.read_configuration()['duration'] == None
    assert daq.connected
    assert daq.configured
    daq.disconnect()
    assert not daq.connected
    assert not daq.configured
    daq.connect()
    assert daq.connected
    assert not daq.configured
    daq.configure(duration=60)
    assert daq.read_configuration()['events'] == None
    assert daq.read_configuration()['duration'] == 60
    assert daq.connected
    assert daq.configured
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
    with pytest.raises(RuntimeError):
        daq.configure()


@pytest.mark.timeout(20)
def test_run_flow(daq):
    """
    We expect a begin without a configure to throw an error.
    Otherwise, we expect the daq to run for the configured time, or the time
    passed into begin.
    We expect that the running stops early if we call stop.
    We expect that we close the run upon calling end_run
    We expect that wait will block the thread until the daq is no longer
    running
    """
    with pytest.raises(RuntimeError):
        daq.begin()
    assert daq.state == 'Disconnected'
    daq.configure(duration=1)
    assert daq.state == 'Configured'
    daq.begin()
    assert daq.state == 'Running'
    time.sleep(1.3)
    assert daq.state == 'Open'
    daq.begin(duration=2)
    assert daq.state == 'Running'
    time.sleep(1.3)
    assert daq.state == 'Running'
    time.sleep(1.3)
    assert daq.state == 'Open'
    daq.end_run()
    assert daq.state == 'Configured'
    daq.configure(duration=60)
    t0 = time.time()
    daq.begin()
    assert daq.state == 'Running'
    daq.stop()
    assert daq.state == 'Open'
    assert time.time() - t0 < 5
    t1 = time.time()
    daq.begin(duration=2)
    assert daq.state == 'Running'
    daq.wait()
    assert daq.state == 'Open'
    assert time.time() - t1 > 2
    daq.begin(duration=60)
    assert daq.state == 'Running'
    daq.pause()
    assert daq.state == 'Open'
    daq.resume()
    assert daq.state == 'Running'
    daq.end_run()
    assert daq.state == 'Configured'


@pytest.mark.timeout(10)
def test_scan(daq):
    """
    We expect that the daq object is usable in a bluesky plan.
    """
    RE = RunEngine({})
    daq.connect()
    daq.configure(duration=60, record=False)
    assert daq.state == 'Configured'

    @fly_during_decorator([daq])
    @stage_decorator([daq])
    @run_decorator()
    def plan(reader):
        for i in range(10):
            assert daq.state == 'Running'
            yield from trigger_and_read([reader])
        assert daq.state == 'Running'

    RE(plan(Reader('test', {'zero': lambda: 0})))

    assert daq.state == 'Configured'
