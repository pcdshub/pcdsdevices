#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in pim that don't change live devices
"""
import pytest

from epics import caget

from pcdsdevices.epics import pim
from conftest import requires_epics


@requires_epics
@pytest.mark.timeout(3)
def test_pim_motor_reads():
    pim6 = pim.PIMMotor("XCS:SB2:PIM6")
    assert(pim6.read())

@requires_epics
@pytest.mark.timeout(3)
def test_pim_motor_blocking_is_bool():
    pim6 = pim.PIMMotor("XCS:SB2:PIM6")
    assert(isinstance(pim6.blocking, bool))

@requires_epics
@pytest.mark.timeout(3)
def test_pim_pulnix_detector_reads():
    dg3 = pim.PIMPulnixDetector("HFX:DG3:CVV:01")
    assert(dg3.read())

@requires_epics
@pytest.mark.timeout(3)
def test_pim_reads():
    dg3_pim = pim.PIM("HFX:DG3:PIM")
    assert(dg3_pim.read())

@requires_epics
@pytest.mark.timeout(3)
def test_pim_fee_instantiates(get_p3h):
    p3h = get_p3h
    assert isinstance(p3h, pim.PIMFee)

@requires_epics
@pytest.mark.timeout(3)
def test_pim_fee_blocking_reads_correctly(get_p3h):
    p3h = get_p3h
    assert p3h.blocking is bool(caget("{0}:POSITION".format(
        p3h._pos_pref)))
