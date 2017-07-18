#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in the HOMS mirror that don't change live devices
"""
import pytest

import numpy as np
from epics import caget 

from pcdsdevices.epics.mirror import OffsetMirror
from conftest import requires_epics

TOL = 5e-4
AVE = 10

@requires_epics
@pytest.mark.timeout(3)
def test_mirror_instantiates_correctly(get_m1h):
    m1h = get_m1h
    assert(isinstance(m1h, OffsetMirror))

@requires_epics
@pytest.mark.timeout(3)
def test_mirror_alpha_reads_correctly(get_m1h):
    m1h = get_m1h
    m1h_alpha = np.array([m1h.alpha for i in range(AVE)])
    ca_alpha = np.array([caget("{0}:RBV".format(m1h.prefix)) for i 
                         in range(AVE)])
    assert np.isclose(m1h_alpha.mean(), ca_alpha.mean(), atol=TOL)

@requires_epics
@pytest.mark.timeout(3)
def test_mirror_x_reads_correctly(get_m1h):
    m1h = get_m1h
    m1h_x = np.array([m1h.x for i in range(AVE)])
    ca_x = np.array([caget("{0}:X:P:RBV".format(m1h._prefix_xy)) 
                     for i in range(AVE)])
    assert np.isclose(m1h_x.mean(), ca_x.mean(), atol=TOL)

@requires_epics
@pytest.mark.timeout(3)
def test_mirror_y_reads_correctly(get_m1h):
    m1h = get_m1h
    m1h_y = np.array([m1h.y for i in range(AVE)])
    ca_y = np.array([caget("{0}:Y:P:RBV".format(m1h._prefix_xy)) 
                     for i in range(AVE)])
    assert np.isclose(m1h_y.mean(), ca_y.mean(), atol=TOL)
