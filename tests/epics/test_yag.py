#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in the yagthat don't change live devices
"""
import pytest

from pcdsdevices.epics.yag import FEEYag

from conftest import requires_epics

@requires_epics
@pytest.mark.timeout(3)
def test_yag_reads():
    p3h = FEEYag("CAMR:FEE1:913:", pos_pref="FEE1:P3H")
    assert(isinstance(p3h, FEEYag))
