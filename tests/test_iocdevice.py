#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test the iocAdmin interface
"""
from pcdsdevices.epics.iocadmin import IocAdmin
from pcdsdevices.epics.iocdevice import IocDevice


def test_device():
    """
    Just make sure that we make the device and it gets an ioc attribute that is
    in iocAdmin instance.
    """
    dev = IocDevice("XCS:USR:MMS:32", ioc="IOC:XCS:USR:DUMB:IMS")
    assert(isinstance(dev.ioc, IocAdmin))
