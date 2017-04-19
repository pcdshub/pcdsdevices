#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for EPICS-spefic base devices
"""
from pcdsdevices.epics import component, device, signal


def test_component():
    """
    Only change here is putting "ioc" as a default add_prefix for
    FormattedComponent.
    """
    class Test:
        pass
    comp = component.FormattedComponent(Test)
    assert("ioc" in comp.add_prefix)


def test_device():
    """
    No changes for now, just make sure we can import something named "Device"
    from this module.
    """
    device.Device


def test_signal():
    """
    No changes for now, just make sure we can import EpicsSignal and
    EpicsSignalRO from here.
    """
    signal.EpicsSignal
    signal.EpicsSignalRO
