#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in lodcm that don't change live devices
"""
from pcdsdevices.epics import lodcm
from conftest import requires_epics


@requires_epics
def test_lodcm_reads():
    lom = lodcm.LODCM("XCS:LODCM", ioc="IOC:XCS:LODCM")
    assert(lom.destination() in dir(lom.light_states))
    assert(lom.destination(line="MAIN") in dir(lom.light_states))
    assert(lom.destination(line="MONO") in dir(lom.light_states))
