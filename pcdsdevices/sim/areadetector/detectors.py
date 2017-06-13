#!/usr/bin/env python
# -*- coding: utf-8 -*-
##########
# Module #
##########
from .cam import PulnixCam
from ..component import Component
from ...epics.areadetector import detectors


class DetectorBase(detectors.DetectorBase):
    pass


class PulnixDetector(detectors.PulnixDetector, DetectorBase):
    cam = Component(PulnixCam, ":")
