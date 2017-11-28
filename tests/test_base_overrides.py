#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test the base classes in the top-level directory.
"""
import time
from threading import Thread

from pcdsdevices import component, device, signal


def test_base_device():
    """
    pcdsdevices.device.Device is expecting to be passed a db_info kwarg with
    metadata and arguments, and it's also expecting to (maybe) get some of
    these arguments (some may have been taken out of kwargs in a child).

    Make sure a device instantiated with these arguments is valid and that we
    can get one of the metadata components back, both through attribute access
    and dictionary access.
    """
    dev = device.Device(prefix="fake_prefix", name='test', z=243, cows=True,
                        db_info=dict(prefix="fake_prefix", z=243, cows=True))
    assert(dev.db.z == 243)
    assert(dev.db.info["z"] == 243)


def wait_and_put(sig_obj, value, wait_time):
    """
    Helper function for setting a signal to a value.
    """
    time.sleep(wait_time)
    sig_obj.put(value)


def wait_and_put_thread(sig_obj, value, wait_time):
    """
    Helper function for setting a signal to a value in a thread.
    """
    set_thread = Thread(target=wait_and_put, args=(sig_obj, value, wait_time))
    set_thread.start()
    return set_thread


def test_base_signal_wait_success():
    """
    Test that waiting for a signal to change took less time than timeout, and
    that the value did change to the desired value.
    """
    sig = signal.Signal(value=0)
    wait_and_put_thread(sig, 1, 1)
    start = time.time()
    assert(sig.get() == 0)
    sig.wait_for_value(1, timeout=2)
    end = time.time()
    duration = end - start
    assert(sig.get() == 1)
    assert(duration < 2)


def test_base_signal_wait_timeout():
    """
    Test that waiting for a signal that doesn't change times out, and the value
    doesn't change in that timeout span if it wasn't changed.
    """
    sig = signal.Signal(value=2)
    wait_and_put_thread(sig, 3, 1)
    assert(sig.get() == 2)
    sig.wait_for_value(1, timeout=0.5)
    assert(sig.get() == 2)


def test_base_signal_wait_context():
    """
    Repeat the success test with the context manager.
    """
    sig = signal.Signal(value=4)
    start = time.time()
    with sig.wait_for_value_context(5, timeout=1):
        sig.put(5)
    end = time.time()
    duration = end - start
    assert(sig.get() == 5)
    assert(duration < 1)


def test_base_signal_wait_transitions():
    """
    Repeat the success test while specifying the old value.
    """
    sig = signal.Signal(value=6)
    wait_and_put_thread(sig, 7, 1)
    start = time.time()
    assert(sig.get() == 6)
    sig.wait_for_value(7, old_value=6, timeout=2)
    end = time.time()
    duration = end - start
    assert(sig.get() == 7)
    assert(duration < 2)


def test_base_signal_wait_transition_timeout():
    """
    Repeat the timeout test with a bad old_value
    """
    sig = signal.Signal(value=8)
    wait_and_put_thread(sig, 9, 1)
    start = time.time()
    assert(sig.get() == 8)
    sig.wait_for_value(9, old_value=4, timeout=3)
    end = time.time()
    duration = end - start
    assert(duration > 2)
