#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import inspect


def get_classes_in_module(module, subcls=None):
    classes = []
    all_classes = inspect.getmembers(module)
    for _, cls in all_classes:
        try:
            if cls.__module__ == module.__name__:
                if subcls is not None:
                    try:
                        if not issubclass(cls, subcls):
                            continue
                    except TypeError:
                        continue
                classes.append(cls)
        except AttributeError:
            pass
    return classes


def connect_rw_pvs(epics_signal):
    """
    Modify an epics signal using fake epics pvs such that writing to the
    write_pv changes the read_pv
    """
    def make_put(original_put, read_pv):
        def put(*args, **kwargs):
            original_put(*args, **kwargs)
            read_pv.put(*args, **kwargs)
        return put
    write_pv = epics_signal._write_pv
    read_pv = epics_signal._read_pv
    write_pv.put = make_put(write_pv.put, read_pv)


def func_wait_true(func, timeout=1, step=0.1):
    """
    For things that don't happen immediately but don't have a good way to wait
    for them. Does a simple timeout loop, returning after timeout or when
    func() is True.
    """
    while not func() and timeout > 0:
        timeout -= step
        time.sleep(step)


def attr_wait_true(obj, attr, timeout=1, step=0.1):
    func_wait_true(lambda: getattr(obj, attr), timeout=timeout, step=step)


def attr_wait_false(obj, attr, timeout=1, step=0.1):
    func_wait_true(lambda: not getattr(obj, attr), timeout=timeout, step=step)


def attr_wait_value(obj, attr, value, delta=0.01, timeout=1, step=0.1):
    func_wait_true(lambda: abs(getattr(obj, attr) - value) < delta,
                   timeout=timeout, step=step)
