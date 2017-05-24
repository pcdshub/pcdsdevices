#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for detectors.
"""
import logging
import ophyd.detectors
import .cam
from .base import ADBase

logger = logging.getLogger(__name__)


class DetectorBase(ophyd.detectors.DetectorBase, ADBase):
    pass


class AreaDetector(ophyd.detectors.AreaDetector, DetectorBase):
    pass


class SimDetector(ophyd.detectors.SimDetector, DetectorBase):
    pass


class AdscDetector(ophyd.detectors.AdscDetector, DetectorBase):
    pass


class AndorDetector(ophyd.detectors.AndorDetector, DetectorBase):
    pass


class Andor3Detector(ophyd.detectors.Andor3Detector, DetectorBase):
    pass


class BrukerDetector(ophyd.detectors.BrukerDetector, DetectorBase):
    pass


class FirewireLinDetector(ophyd.detectors.FirewireLinDetector, DetectorBase):
    pass


class FirewireWinDetector(ophyd.detectors.FirewireWinDetector, DetectorBase):
    pass


class LightFieldDetector(ophyd.detectors.LightFieldDetector, DetectorBase):
    pass


class Mar345Detector(ophyd.detectors.Mar345Detector, DetectorBase):
    pass


class MarCCDDetector(ophyd.detectors.MarCCDDetector, DetectorBase):
    pass


class PerkinElmerDetector(ophyd.detectors.PerkinElmerDetector, DetectorBase):
    pass


class PSLDetector(ophyd.detectors.PSLDetector, DetectorBase):
    pass


class PilatusDetector(ophyd.detectors.PilatusDetector, DetectorBase):
    pass


class PixiradDetector(ophyd.detectors.PixiradDetector, DetectorBase):
    pass


class PointGreyDetector(ophyd.detectors.PointGreyDetector, DetectorBase):
    pass


class ProsilicaDetector(ophyd.detectors.ProsilicaDetector, DetectorBase):
    pass


class PvcamDetector(ophyd.detectors.PvcamDetector, DetectorBase):
    pass


class RoperDetector(ophyd.detectors.RoperDetector, DetectorBase):
    pass


class URLDetector(ophyd.detectors.URLDetector, DetectorBase):
    pass
