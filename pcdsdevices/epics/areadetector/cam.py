#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides for AreaDetector Cam.
"""
import logging
import ophyd.cam

from .base import ADBase

logger = logging.getLogger(__name__)


class CamBase(ophyd.cam.CamBase, ADBase):
    pass


class AreaDetectorCam(ophyd.cam.AreaDetectorCam, Cambase):
    pass


class SimDetectorCam(ophyd.cam.SimDetectorCam, Cambase):
    pass


class AdscDetectorCam(ophyd.cam.AdscDetectorCam, Cambase):
    pass


class AndorDetectorCam(ophyd.cam.AndorDetectorCam, Cambase):
    pass


class Andor3DetectorCam(ophyd.cam.Andor3DetectorCam, Cambase):
    pass


class BrukerDetectorCam(ophyd.cam.BrukerDetectorCam, Cambase):
    pass


class FirewireLinDetectorCam(ophyd.cam.FirewireLinDetectorCam, Cambase):
    pass


class FirewireWinDetectorCam(ophyd.cam.FirewireWinDetectorCam, Cambase):
    pass


class LightFieldDetectorCam(ophyd.cam.LightFieldDetectorCam, Cambase):
    pass


class Mar345DetectorCam(ophyd.cam.Mar345DetectorCam, Cambase):
    pass


class MarCCDDetectorCam(ophyd.cam.MarCCDDetectorCam, Cambase):
    pass


class PcoDetectorCam(ophyd.cam.PcoDetectorCam, Cambase):
    pass


class PcoDetectorIO(ophyd.cam.PcoDetectorIO, ADBase):
    pass


class PcoDetectorSimIO(ophyd.cam.PcoDetectorSimIO, ADBase):
    pass


class PerkinElmerDetectorCam(ophyd.cam.PerkinElmerDetectorCam, Cambase):
    pass


class PSLDetectorCam(ophyd.cam.PSLDetectorCam, Cambase):
    pass


class PilatusDetectorCam(ophyd.cam.PilatusDetectorCam, Cambase):
    pass


class PixiradDetectorCam(ophyd.cam.PixiradDetectorCam, Cambase):
    pass


class PointGreyDetectorCam(ophyd.cam.PointGreyDetectorCam, Cambase):
    pass


class ProsilicaDetectorCam(ophyd.cam.ProsilicaDetectorCam, Cambase):
    pass


class PvcamDetectorCam(ophyd.cam.PvcamDetectorCam, Cambase):
    pass


class RoperDetectorCam(ophyd.cam.RoperDetectorCam, Cambase):
    pass


class URLDetectorCam(ophyd.cam.URLDetectorCam, Cambase):
    pass


