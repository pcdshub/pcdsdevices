import logging

from ophyd.device import Component as Cpt
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.areadetector.base import EpicsSignalWithRBV

from pcdsdevices.areadetector.detectors import PCDSAreaDetectorTyphos

logger = logging.getLogger(__name__)


class ThorlabsWfs40(PCDSAreaDetectorTyphos):
    """Class to implement a Thorlabs WFS40 Wavefront sensor."""

    beam_status = Cpt(EpicsSignalRO, 'StatHighAmbientLight', kind='normal')

    pupil_centroid_x = Cpt(EpicsSignalWithRBV, 'PupilCentroidX', kind='config')
    pupil_centroid_y = Cpt(EpicsSignalWithRBV, 'PupilCentroidY', kind='config')
    pupil_diameter_x = Cpt(EpicsSignalWithRBV, 'PupilDiameterX', kind='config')
    pupil_diameter_y = Cpt(EpicsSignalWithRBV, 'PupilDiameterY', kind='config')

    use_beam_centroid = Cpt(EpicsSignal, 'UseBeamCentroid', kind='normal')
    use_beam_diameter = Cpt(EpicsSignal, 'UseBeamDiameter', kind='normal')
    use_circular_pupil = Cpt(EpicsSignal, 'UseCircularPupil', kind='normal')

    beam_centroid_x = Cpt(EpicsSignalRO, 'BeamCentroidX_RBV', kind='normal')
    beam_centroid_y = Cpt(EpicsSignalRO, 'BeamCentroidY_RBV', kind='normal')
    beam_diameter_x = Cpt(EpicsSignalRO, 'BeamDiameterX_RBV', kind='normal')
    beam_diameter_y = Cpt(EpicsSignalRO, 'BeamDiameterY_RBV', kind='normal')
    radius_of_curvature = Cpt(EpicsSignalRO, 'RadiusOfCurvature_RBV',
                              kind='normal')

    fourier_m = Cpt(EpicsSignalRO, 'FourierM_RBV', kind='config')
    fourier_j0 = Cpt(EpicsSignalRO, 'FourierJ0_RBV', kind='config')
    fourier_j45 = Cpt(EpicsSignalRO, 'FourierJ45_RBV', kind='config')

    number_of_exposures = Cpt(EpicsSignal, 'NumExposures', kind='config')

    _xmin = Cpt(EpicsSignalRO, 'Xmin', kind='config')
    _ymin = Cpt(EpicsSignalRO, 'Ymin', kind='config')
    _dmin = Cpt(EpicsSignalRO, 'Dmin', kind='config')
