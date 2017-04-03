#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test methods shared between all devices
We basically just need to make sure that "something" is returned for every
component when we look at values from our live IOCs.

Errors will be one of:
    1. Major bug
    2. Our interface is wrong
    3. The IOC has changed or is down
"""


def test_get(all_devices):
    values = all_devices.get()
    for val in values:
        assert(val is not None)


def recursive_not_none(val):
    if isinstance(val, dict):
        recursive_not_none(list(val.values()))
    elif isinstance(val, (list, tuple)):
        for v in val:
            recursive_not_none(v)
    else:
        assert(val is not None)


def test_get_nested(all_devices):
    values = all_devices.get()
    recursive_not_none(values)
