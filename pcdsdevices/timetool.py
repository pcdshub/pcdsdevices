"""
Module for Timetool classes.
"""
from collections import defaultdict

from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt

from .areadetector.detectors import PCDSAreaDetector
from .epics_motor import IMS
from .inout import CombinedInOutRecordPositioner


class Timetool(CombinedInOutRecordPositioner):
    """
    Timetool motion with x- and y-motion motors.

    The PVs for each of the motors will be inferred from the base prefix but
    the area detector's PV must be passed as a keyword argument, as labeled.

    Parameters
    ----------
    prefix : str
        The EPICS base PV of the Timetool.

    name : str
        A name to refer to the device.

    prefix_det : str
        The EPICS base PV of the detector.
    """

    # Clear the default in/out state list. List will be populated during
    # init to grab appropriate state names for each target.
    states_list = []
    # In should be everything except state 0 (Unknown) and state 1 (Out)
    _in_if_not_out = True

    detector = FCpt(PCDSAreaDetector, '{self._prefix_det}', kind='normal')

    def __init__(self, prefix, *, name, prefix_det, **kwargs):
        self._prefix_det = prefix_det
        # Set default transmission
        # Done this way because states are still unknown at this point
        # Assume that having any target in gives transmission 0.8
        self._transmission = defaultdict(lambda state: 0.8
                                         if state in self.in_states
                                         else (1 if state in self.out_states
                                               else 0))
        super().__init__(prefix, name=name, **kwargs)


class TimetoolWithNav(Timetool):
    """
    Timetool motion with zoom, focus, and x- & y-motion motors.

    The PVs for each of the motors will be inferred from the base prefix but
    the area detector's PV must be passed as a keyword argument, as labeled.

    Parameters
    ----------
    prefix : str
        The EPICS base PV of the Timetool.

    name : str
        A name to refer to the device.

    prefix_det : str
        The EPICS base PV of the detector.
    """

    zoom_motor = Cpt(IMS, ':ZOOM_MOTOR', kind='normal')
    focus_motor = Cpt(IMS, ':FOCUS_MOTOR', kind='normal')
