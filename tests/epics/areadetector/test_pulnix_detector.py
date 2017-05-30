#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in a pulnix detector that doesnt change live pvs.
"""
import pytest

from pcdsdevices.epics.areadetector.detectors import PulnixDetector

from conftest import requires_epics

@requires_epics
@pytest.mark.timeout(3)
def test_pulnix_reads():
    dg3 = PulnixDetector("HFX:DG3:CVV:01")
    assert(isinstance(dg3, PulnixDetector))
