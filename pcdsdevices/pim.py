"""
Profile Intensity Monitor Classes

This module contains all the classes relating to the profile intensity monitor
classes at the user level. A PIM will usually have at least a motor to control
yag position and a camera to view the yag.

Classes Implemented here are as follows:

PIMPulnixDetector
    Pulnix detector with only the plugins used by the PIMs.

PIMMotor
    Profile intensity monitor motor that moves the yag and diode into and out
    of the beam.

PIM
    High level profile intensity monitor class that inherits from PIMMotor and
    has a PIMPulnixDetector as a component.
"""
import logging

from ophyd import Component, FormattedComponent

from .state import StateRecordPositioner
from .areadetector.detectors import PulnixDetector
from .areadetector.plugins import ImagePlugin, StatsPlugin

logger = logging.getLogger(__name__)


class PIMPulnixDetector(PulnixDetector):
    """
    Pulnix detector that is used in the PIM. Plugins should be added on an as
    needed basis here.
    """
    image1 = Component(ImagePlugin, ":IMAGE1:", read_attrs=['array_data'])
    image2 = Component(ImagePlugin, ":IMAGE2:", read_attrs=['array_data'])
    stats2 = Component(StatsPlugin, ":Stats2:", read_attrs=['centroid',
                                                            'mean_value'])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.image1.stage_sigs[self.image1.nd_array_port] = 'CAM'
        self.image1.stage_sigs[self.image1.blocking_callbacks] = 'Yes'
        self.image1.stage_sigs[self.image1.enable] = 1

        self.stats2.stage_sigs[self.stats2.nd_array_port] = 'CAM'
        self.stats2.stage_sigs[self.stats2.blocking_callbacks] = 'Yes'
        self.stats2.stage_sigs[self.stats2.compute_statistics] = 'Yes'
        self.stats2.stage_sigs[self.stats2.compute_centroid] = 'Yes'
        self.stats2.stage_sigs[self.stats2.centroid_threshold] = 200
        self.stats2.stage_sigs[self.stats2.min_callback_time] = 0.0
        self.stats2.stage_sigs[self.stats2.enable] = 1


class PIMMotor(StateRecordPositioner):
    """
    Standard position monitor motor that can move the stage to insert the yag
    or diode, or retract it from the beam path.
    """
    states_list = ['DIODE', 'YAG', 'OUT']
    _states_alias = {'YAG': 'IN'}

    def stage(self):
        self._original_vals[self.state] = self.state.value
        return super().stage()


class PIM(PIMMotor):
    """
    Full profile intensity monitor including the motor to move the yag, and the
    detector to view it.

    Parameters
    ----------
    prefix : str
        The EPICS base of the motor

    name : str
        A name to refer to the device

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be inferred from
        the motor prefix
    """
    detector = FormattedComponent(PIMPulnixDetector, "{self._prefix_det}",
                                  read_attrs=['stats2'])

    _default_read_attrs = ['state', 'readback', 'detector']

    def __init__(self, prefix, *, name, prefix_det=None, **kwargs):
        # Infer the detector PV from the motor PV
        if not prefix_det:
            self._section = prefix.split(":")[0]
            self._imager = prefix.split(":")[1]
            self._prefix_det = "{0}:{1}:CVV:01".format(
                self._section, self._imager)
        else:
            self._prefix_det = prefix_det
        super().__init__(prefix, name=name, **kwargs)
