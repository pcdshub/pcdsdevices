#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in a opal detector that doesnt change live pvs.
"""
import pytest

from pcdsdevices.epics.areadetector.detectors import FeeOpalDetector

from conftest import requires_epics

@requires_epics
@pytest.mark.timeout(3)
def test_fee_opal_reads():
    p3h = FeeOpalDetector("CAMR:FEE1:913")
    assert(isinstance(p3h, FeeOpalDetector))
