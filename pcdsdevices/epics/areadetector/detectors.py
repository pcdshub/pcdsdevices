#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PCDS detectors and overrides for ophyd detectors.
"""
import logging

from ophyd import detectors

from . import cam
from .base import (ADBase, ADComponent)
from ..component import Component

logger = logging.getLogger(__name__)

__all__ = ['DetectorBase',
           'AreaDetector',
           'PulnixDetector',
           'FEEOpalDetector',
           'AdscDetector',
           'Andor3Detector',
           'AndorDetector',
           'BrukerDetector',
           'FirewireLinDetector',
           'FirewireWinDetector',
           'LightFieldDetector',
           'Mar345Detector',
           'MarCCDDetector',
           'PerkinElmerDetector',
           'PilatusDetector',
           'PixiradDetector',
           'PointGreyDetector',
           'ProsilicaDetector',
           'PSLDetector',
           'PvcamDetector',
           'RoperDetector',
           'SimDetector',
           'URLDetector',
]


class DetectorBase(detectors.DetectorBase, ADBase):
    pass


class AreaDetector(detectors.AreaDetector, DetectorBase):
    pass


class PulnixDetector(DetectorBase):
    cam = ADComponent(cam.PulnixCam, ":")


class FEEOpalDetector(DetectorBase):
    cam = ADComponent(cam.FEEOpalCam, ":")


class SimDetector(detectors.SimDetector, DetectorBase):
    pass


class AdscDetector(detectors.AdscDetector, DetectorBase):
    pass


class AndorDetector(detectors.AndorDetector, DetectorBase):
    pass


class Andor3Detector(detectors.Andor3Detector, DetectorBase):
    pass


class BrukerDetector(detectors.BrukerDetector, DetectorBase):
    pass


class FirewireLinDetector(detectors.FirewireLinDetector, DetectorBase):
    pass


class FirewireWinDetector(detectors.FirewireWinDetector, DetectorBase):
    pass


class LightFieldDetector(detectors.LightFieldDetector, DetectorBase):
    pass


class Mar345Detector(detectors.Mar345Detector, DetectorBase):
    pass


class MarCCDDetector(detectors.MarCCDDetector, DetectorBase):
    pass


class PerkinElmerDetector(detectors.PerkinElmerDetector, DetectorBase):
    pass


class PSLDetector(detectors.PSLDetector, DetectorBase):
    pass


class PilatusDetector(detectors.PilatusDetector, DetectorBase):
    pass


class PixiradDetector(detectors.PixiradDetector, DetectorBase):
    pass


class PointGreyDetector(detectors.PointGreyDetector, DetectorBase):
    pass


class ProsilicaDetector(detectors.ProsilicaDetector, DetectorBase):
    pass


class PvcamDetector(detectors.PvcamDetector, DetectorBase):
    pass


class RoperDetector(detectors.RoperDetector, DetectorBase):
    pass


class URLDetector(detectors.URLDetector, DetectorBase):
    pass
