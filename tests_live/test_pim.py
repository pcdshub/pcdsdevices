#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test functions in pim that don't change live devices
"""
import pytest

import numpy as np
from epics import caget

from pcdsdevices.epics import pim
from conftest import requires_epics
from pcdsdevices.epics.areadetector.plugins import PluginBase


@requires_epics
@pytest.mark.timeout(3)
def test_pim_motor_instantiates(get_dg3_mot):
    dg3_mot = get_dg3_mot
    assert(isinstance(dg3_mot, pim.PIMMotor))

@requires_epics
@pytest.mark.timeout(3)
def test_pim_motor_blocking_reads_correctly(get_dg3_mot):
    dg3_mot = get_dg3_mot
    assert(isinstance(dg3_mot.blocking, bool))
    assert(dg3_mot.blocking is not bool(caget("{0}:OUT".format(
        dg3_mot.prefix))))
    
@requires_epics
@pytest.mark.timeout(3)
def test_pim_pulnix_detector_instantiates(get_dg3_det):
    dg3_det = get_dg3_det
    assert(isinstance(dg3_det, pim.PIMPulnixDetector))

@requires_epics
@pytest.mark.timeout(3)
def test_pim_pulnix_detector_plugins_instantiate(get_dg3_det):
    dg3_det = get_dg3_det
    plugins = ['image2', 'stats1', 'stats2', 'proc1']
    for plugin in plugins:
        assert(hasattr(dg3_det, plugin))
        assert(isinstance(getattr(dg3_det, plugin), PluginBase))

@requires_epics
@pytest.mark.timeout(3)
def test_pim_instantiates(get_dg3_pim):
    dg3_pim = get_dg3_pim
    assert(isinstance(dg3_pim, pim.PIM))

@requires_epics
@pytest.mark.timeout(3)
def test_pim_image(get_dg3_pim):
    dg3_pim = get_dg3_pim
    assert(isinstance(dg3_pim.detector.image, np.ndarray))
    assert(dg3_pim.detector.image.any())

@requires_epics
@pytest.mark.timeout(3)
def test_pim_acquiring_reads_correctly(get_dg3_pim):
    dg3_pim = get_dg3_pim
    assert(isinstance(dg3_pim.detector.acquiring, bool))
    assert(dg3_pim.detector.acquiring is bool(caget("{0}:{1}:CVV:01:Acquire_RBV".format(
        dg3_pim._section, dg3_pim._imager))))

@requires_epics
@pytest.mark.timeout(3)
def test_pim_centroids(get_dg3_pim):
    dg3_pim = get_dg3_pim
    try:
        dg3_pim.check_camera()
        assert([float(c) for c in dg3_pim.centroid])
        assert(float(dg3_pim.centroid_x))
        assert(float(dg3_pim.centroid_y))
    except (pim.NotInsertedError, pim.NotAcquiringError):
        pass

@requires_epics
@pytest.mark.timeout(3)
def test_pim_fee_instantiates(get_p3h_pim):
    p3h_pim = get_p3h_pim
    assert isinstance(p3h_pim, pim.PIMFee)

@requires_epics
@pytest.mark.timeout(3)
def test_pim_fee_blocking_reads_correctly(get_p3h_pim):
    p3h_pim = get_p3h_pim
    assert(isinstance(p3h_pim.blocking, bool))
    assert(p3h_pim.blocking is bool(caget("{0}:POSITION".format(
        p3h_pim._pos_pref))))

# @requires_epics
# @pytest.mark.timeout(3)
# def test_pim_fee_image(get_p3h_pim):
#     p3h_pim = get_p3h_pim
#     assert(isinstance(p3h_pim.detector.image, np.ndarray))
#     assert(p3h_pim.detector.image.any())

# @requires_epics
# @pytest.mark.timeout(3)
# def test_pim_fee_acquiring_reads_correctly(get_p3h_pim):
#     p3h_pim = get_p3h_pim
#     assert(isinstance(p3h_pim.detector.acquiring, bool))
#     assert(p3h_pim.detector.acquiring is bool(caget("{0}:Acquire".format(
#         p3h_pim.detector.prefix))))

# # Uncomment this once centroids is implemented for fee pims
# @requires_epics
# @pytest.mark.timeout(3)
# def test_pim_fee_centroids(get_p3h_pim):
#     p3h_pim = get_p3h_pim
#     try:
#         p3h_pim.check_camera():    
#         assert([float(c) for c in p3h_pim.centroid])
#         assert(float(p3h_pim.centroid_x))
#         assert(float(p3h_pim.centroid_y))
#     except (pim.NotInsertedError, pim.NotAcquiringError):
#         pass
