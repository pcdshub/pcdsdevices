"""
PCDS detectors and overrides for ophyd detectors.

All components at the detector level such as plugins  or image processing
functions needed by all instances of a detector are added here.
"""
import logging

from ophyd.areadetector import cam
from ophyd.areadetector.base import ADComponent
from ophyd.areadetector.detectors import DetectorBase
from ophyd.device import Component as Cpt

from .plugins import ImagePlugin, StatsPlugin

logger = logging.getLogger(__name__)


__all__ = ['AreaDetector',
           'DefaultAreaDetector']


class AreaDetector(DetectorBase):
    """
    Standard area detector with no plugins.
    """
    cam = ADComponent(cam.CamBase, ":")


class DefaultAreaDetector(AreaDetector):
    """
    Standard area detector with standard plugins.

    Geared towards analyzing a beam spot.

    image2: reduced rate image
    stats2: reduced rate stats
    """
    image2 = Cpt(ImagePlugin, ':IMAGE1:', read_attrs=['array_data'])
    stats2 = Cpt(StatsPlugin, ':Stats2:', read_attrs=['centroid',
                                                      'mean_value',
                                                      'sigma_x',
                                                      'sigma_y'])

    def __init__(self, *args, **kwargs):
        super.__init__(*args, **kwargs)
        self.image1.stage_sigs[self.image1.enable] = 1
        self.stats2.stage_sigs[self.stats2.enable] = 1
        self.stats2.stage_sigs[self.stats2.compute_statistics] = 'Yes'
        self.stats2.stage_sigs[self.stats2.compute_centroid] = 'Yes'
