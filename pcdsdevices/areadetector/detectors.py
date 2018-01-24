"""
PCDS detectors and overrides for ophyd detectors.

All components at the detector level such as plugins  or image processing
functions needed by all instances of a detector are added here.
"""
import logging

from ophyd.areadetector import cam
from ophyd.areadetector.base import ADComponent
from ophyd.areadetector.detectors import DetectorBase

from .cam import FeeOpalCam

logger = logging.getLogger(__name__)


__all__ = ['PulnixDetector',
           'FeeOpalDetector']


class PulnixDetector(DetectorBase):
    """
    Standard pulnix detector.
    """
    cam = ADComponent(cam.CamBase, ":")


class FeeOpalDetector(DetectorBase):
    """
    Opal detector that in the FEE running using Dehong's IOC.
    """
    cam = ADComponent(FeeOpalCam, ":")
