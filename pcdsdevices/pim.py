"""
Profile Intensity Monitor Classes

This module contains all the classes relating to the profile intensity monitor
classes at the user level. A PIM will usually have at least a motor to control
yag position and a camera to view the yag.
"""
import logging

from ophyd import FormattedComponent as FCpt

from .areadetector.detectors import PCDSAreaDetector
from .inout import InOutRecordPositioner

logger = logging.getLogger(__name__)


class PIMMotor(InOutRecordPositioner):
    """
    Standard position monitor motor.

    This can move the stage to insert the yag
    or diode, or retract from the beam path.
    """
    states_list = ['DIODE', 'YAG', 'OUT']
    in_states = ['YAG', 'DIODE']

    _states_alias = {'YAG': 'IN'}
    # QIcon for UX
    _icon = 'fa.camera-retro'

    def stage(self):
        """
        Save the original position to be restored on `unstage`.
        """
        self._original_vals[self.state] = self.state.value
        return super().stage()


class PIM(PIMMotor):
    """
    Profile intensity monitor, fully motorized and with a detector.

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
    detector = FCpt(PCDSAreaDetector, "{self._prefix_det}", kind='normal')
    tab_whitelist = ["detector"]

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
