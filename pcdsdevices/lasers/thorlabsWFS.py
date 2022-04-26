import logging

from ophyd.device import Component as Cpt
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.areadetector.base import EpicsSignalWithRBV, NDDerivedSignal

from pcdsdevices.areadetector.detectors import PCDSAreaDetectorTyphosTrigger

logger = logging.getLogger(__name__)


class ThorlabsWfs40(PCDSAreaDetectorTyphosTrigger):
    """Class to implement a Thorlabs WFS40 Wavefront sensor."""
    # Beam Status values
    ambient_light = Cpt(EpicsSignalRO, 'StatHighAmbientLight', kind='config',
                        doc='Status: Ambient light too high')
    power_high = Cpt(EpicsSignalRO, 'StatPowerHigh', kind='config',
                     doc='Status: power too high status')
    power_low = Cpt(EpicsSignalRO, 'StatPowerLow', kind='config',
                    doc='Status: power too low')
    low_contrast = Cpt(EpicsSignalRO, 'StatLowSpotContrast', kind='config',
                       doc='Status: contrast too low')
    low_spots = Cpt(EpicsSignalRO, 'StatNotEnoughSpots', kind='config',
                    doc='Status: too few spots')
    high_spots = Cpt(EpicsSignalRO, 'StatTooMuchSpots', kind='config',
                     doc='Status: too many spots')
    trigger_wait = Cpt(EpicsSignalRO, 'StatTriggerWait', kind='config',
                       doc='Status: waiting for trigger')
    cam_ready = Cpt(EpicsSignalRO, 'StatCameraReady', kind='config',
                    doc='Status: camera ready')
    pupil_defined = Cpt(EpicsSignalRO, 'StatPupilDefined', kind='config',
                        doc='Status: pupil defined')

    pupil_centroid_x = Cpt(EpicsSignalWithRBV, 'PupilCentroidX', kind='config',
                           doc='Est. pupil centroid X')
    pupil_centroid_y = Cpt(EpicsSignalWithRBV, 'PupilCentroidY', kind='config',
                           doc='Est. pupil centroid Y')
    pupil_diameter_x = Cpt(EpicsSignalWithRBV, 'PupilDiameterX', kind='config',
                           doc='Pupil diameter X')
    pupil_diameter_y = Cpt(EpicsSignalWithRBV, 'PupilDiameterY', kind='config',
                           doc='Pupil diameter Y')
    use_beam_centroid = Cpt(EpicsSignal, 'UseBeamCentroid', kind='config',
                            doc='Flag to use beam centroid')
    use_beam_diameter = Cpt(EpicsSignal, 'UseBeamDiameter', kind='config',
                            doc='Flag to use beam diameter')
    use_circular_pupil = Cpt(EpicsSignal, 'UseCircularPupil', kind='config',
                             doc='Flag to use circular pupil')

    beam_centroid_x = Cpt(EpicsSignalRO, 'BeamCentroidX_RBV', kind='normal',
                          doc='Measured beam centroid X')
    beam_centroid_y = Cpt(EpicsSignalRO, 'BeamCentroidY_RBV', kind='normal',
                          doc='Measured beam centroid Y')
    beam_diameter_x = Cpt(EpicsSignalRO, 'BeamDiameterX_RBV', kind='normal',
                          doc='Measured beam diameter in X')
    beam_diameter_y = Cpt(EpicsSignalRO, 'BeamDiameterY_RBV', kind='normal',
                          doc='Measured beam diameter in Y')
    radius_of_curvature = Cpt(EpicsSignalRO, 'RadiusOfCurvature_RBV',
                              kind='normal',
                              doc='Measured beam radius of curvature')

    fourier_m = Cpt(EpicsSignalRO, 'FourierM_RBV', kind='config',
                    doc='Fourier M component')
    fourier_j0 = Cpt(EpicsSignalRO, 'FourierJ0_RBV', kind='config',
                     doc='Fourier J0 component')
    fourier_j45 = Cpt(EpicsSignalRO, 'FourierJ45_RBV', kind='config',
                      doc='Fourier J45 component')

    number_of_exposures = Cpt(EpicsSignal, 'NumExposures', kind='config',
                              doc='Number of images to average for calcs')

    # Wavefront data
    wavefront_data = Cpt(EpicsSignal, 'Wavefront_RBV', kind='omitted',
                         doc='Raw wavefront data array')
    wavefront = Cpt(NDDerivedSignal, derived_from='wavefront_data',
                    doc='Shaped wavefront image',
                    shape=(80, 80, 0),
                    num_dimensions=2,
                    kind='normal')
