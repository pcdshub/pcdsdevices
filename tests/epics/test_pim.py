#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in pim that don't change live devices
"""
from pcdsdevices.epics import pim
from conftest import requires_epics


@requires_epics
def test_pim_reads():
    pim6 = pim.PIM("XCS:SB2:PIM6", ioc="IOC:XCS:SB2:PIM06:IMS")
    assert(isinstance(pim6.blocking, bool))
