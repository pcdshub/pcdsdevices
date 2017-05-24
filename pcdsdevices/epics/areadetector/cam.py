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


class AreaDetectorCam(ophyd.cam. , Cambase):
    pass


class SimDetectorCam(ophyd.cam. , Cambase):
    pass


class AdscDetectorCam(ophyd.cam. , Cambase):
    pass


class AndorDetectorCam(ophyd.cam. , Cambase):
    pass


class Andor3DetectorCam(ophyd.cam. , Cambase):
    pass


class BrukerDetectorCam(ophyd.cam. , Cambase):
    pass


class FirewireLinDetectorCam(ophyd.cam. , Cambase):
    pass


class FirewireWinDetectorCam(ophyd.cam. , Cambase):
    pass


class LightFieldDetectorCam(ophyd.cam. , Cambase):
    pass


class Mar345DetectorCam(ophyd.cam. , Cambase):
    pass


class MarCCDDetectorCam(ophyd.cam. , Cambase):
    pass


class PcoDetectorCam(ophyd.cam. , Cambase):
    pass


class PcoDetectorIO(ADBase):
    pass


class PcoDetectorSimIO(ADBase):
    pass


class PerkinElmerDetectorCam(ophyd.cam. , Cambase):
    pass


class PSLDetectorCam(ophyd.cam. , Cambase):
    pass


class PilatusDetectorCam(ophyd.cam. , Cambase):
    pass


class PixiradDetectorCam(ophyd.cam. , Cambase):
    pass


class PointGreyDetectorCam(ophyd.cam. , Cambase):
    pass


class ProsilicaDetectorCam(ophyd.cam. , Cambase):
    pass


class PvcamDetectorCam(ophyd.cam. , Cambase):
    pass


class RoperDetectorCam(ophyd.cam. , Cambase):
    pass


class URLDetectorCam(ophyd.cam. , Cambase):
    pass


