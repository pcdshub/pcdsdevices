#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in attenuator that don't change live devices
"""
from pcdsdevices.epics import attenuator
from conftest import requires_epics


@requires_epics
def test_filter_reads():
    filt = attenuator.Filter("XCS:ATT:01")
    assert(filt.value in dir(filt.filter_states))
    assert(filt.stuck in dir(filt.stuck_enum))
    assert(isinstance(filt.thickness, float))


@requires_epics
def test_att_reads():
    n = 10
    att = attenuator.Attenuator("XCS:ATT", n_filters=n, ioc="IOC:XCS:ATT")
    assert(isinstance(att(), float))
    assert(isinstance(att.get_transmission(), float))
    assert(isinstance(att.get_transmission(use3rd=True), float))
    assert(isinstance(att._thickest_filter(), attenuator.Filter))
    max_thick = att._thickest_filter().thickness
    thicknesses = []
    for i in range(n):
        thicknesses.append(getattr(att, "filter{}".format(i+1)).thickness)
    assert(max_thick in thicknesses)
    for t in thicknesses:
        assert(max_thick >= t)
