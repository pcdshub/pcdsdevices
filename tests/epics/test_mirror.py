#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in attenuator that don't change live devices
"""
import pytest

from pcdsdevices.epics.mirror import Mirror

from conftest import requires_epics

@requires_epics
@pytest.mark.timeout(3)
def test_mirror_reads():
    m1h = Mirror("MIRR:FEE1:M1H", ioc="IOC:FEE:HOMS")
    assert(isinstance(m1h, Mirror))
