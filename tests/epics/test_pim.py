#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in pim that don't change live devices
"""
import pytest

from pcdsdevices.epics import pim

from conftest import requires_epics


@requires_epics
@pytest.mark.timeout(3)
def test_pim_reads():
    pim6 = pim.PIM("XCS:SB2:PIM6")
    assert(isinstance(pim6.blocking, bool))

@requires_epics
@pytest.mark.timeout(3)
def test_pim_imager_reads():
    dg3 = pim.PIMYag("HFX:DG3:PIM", imager="HFX:DG3:CVV:01")

