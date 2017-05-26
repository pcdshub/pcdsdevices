#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in the HOMS mirror that don't change live devices
"""
import pytest

from pcdsdevices.epics.mirror import OffsetMirror

from conftest import requires_epics

@requires_epics
@pytest.mark.timeout(3)
def test_mirror_reads():
    m1h = OffsetMirror("MIRR:FEE1:M1H",  section="611")
    assert(isinstance(m1h, OffsetMirror))
