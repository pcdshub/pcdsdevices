import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device 
from ophyd.signal import EpicsSignal, EpicsSignalRO

from pcdsdevices.areadetector.detectors import PCDSAreaDetectorBase

class ThorlabsWfs40(PCDSAreaDetectorBase):
    """Class to implement a Thorlabs WFS40 Wavefront sensor."""

    pupil_centroid_x = Cpt(EpicsSignal, 'PupilCentroidX', kind='config')
    pupil_centroid_y = Cpt(EpicsSignal, 'PupilCentroidY', kind='config')
    pupil_diameter_x = Cpt(EpicsSignal, 'PupilDiameterX', kind='config')
    pupil_diameter_y = Cpt(EpicsSignal, 'PupilDiameterY', kind='config')

    pupil_centroid_x_rbv = Cpt(EpicsSignal, 'PupilCentroidX_RBV',
                               kind='normal')
    pupil_centroid_y_rbv = Cpt(EpicsSignal, 'PupilCentroidY_RBV',
                               kind='normal')
    pupil_diameter_x_rbb = Cpt(EpicsSignal, 'PupilDiameterX_RBV',
                               kind='normal')
    pupil_diameter_y_rbv = Cpt(EpicsSignal, 'PupilDiameterY_RBV',
                                kind='normal')

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
