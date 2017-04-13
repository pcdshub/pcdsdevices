#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test methods shared between all devices
We basically just need to make sure that "something" is returned for every
component when we look at values from our live IOCs.

None should only be returned if something we asked for does not exist.
Devices should know to not make the component if we didn't pass the argument.`

Errors will be one of:
    1. Major bug
    2. Our interface is wrong
    3. The IOC has changed or is down
"""
import pytest
try:
    import epics
    pv = epics.PV("XCS:USR:MMS:01")
    try:
        val = pv.get()
    except:
        val = None
except:
    val = None
epics_subnet = val is not None
requires_epics = pytest.mark.skipif(not epics_subnet,
                                    reason="Could not connect to sample PV")


@requires_epics
def test_get(all_devices):
    values = all_devices.get()
    for name, val in values._asdict().items():
        assert val is not None, "Failed to find {}".format(name)


def recursive_not_none(namedtuple, name=""):
    for key, value in namedtuple._asdict().items():
        name = "{}_{}".format(name, key).strip("_")
        if hasattr(value, "_asdict"):
            recursive_not_none(value, name)
        else:
            assert val is not None, "Failed to find {}".format(name)


@requires_epics
def test_get_nested(all_devices):
    values = all_devices.get()
    recursive_not_none(values)
