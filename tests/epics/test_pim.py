#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in pim that don't change live devices
"""
import pytest

from pcdsdevices.epics import pim

from conftest import requires_epics


# @requires_epics
# @pytest.mark.timeout(3)
# def test_pim_motor_reads():
#     pim6 = pim.PIMMotor("XCS:SB2:PIM6")
#     assert(pim6.read())

# @requires_epics
# @pytest.mark.timeout(3)
# def test_pim_motor_blocking_is_bool():
#     pim6 = pim.PIMMotor("XCS:SB2:PIM6")
#     assert(isinstance(pim6.blocking, bool))

# @requires_epics
# @pytest.mark.timeout(3)
# def test_pim_pulnix_detector_reads():
#     dg3 = pim.PIMPulnixDetector("HFX:DG3:CVV:01")
#     assert(dg3.read())

# @requires_epics
# @pytest.mark.timeout(3)
# def test_pim_reads():
#     dg3_pim = pim.PIM("HFX:DG3:PIM", imager="HFX:DG3:CVV:01")
#     assert(dg3_pim.read())

@requires_epics
@pytest.mark.timeout(3)
def test_pim_fee_reads():
    p3h = pim.PIMFee("CAMR:FEE1:913:", pos_pref="FEE1:P3H")
    assert isinstance(p3h, pim.PIMFee)
