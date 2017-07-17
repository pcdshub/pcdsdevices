#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest

try:
    import epics
    pv = epics.PV("XCS:USR:MMS:01")
    try:
        val = pv.get()
    except:
        val = None
except:
    val = None
epics_subnet = val is not None
requires_epics = pytest.mark.skipif(not epics_subnet,
                                    reason="Could not connect to sample PV")

