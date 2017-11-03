#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
