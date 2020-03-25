"""
Module for Timetool classes
"""
from ophyd.device import FormattedComponent as FCpt

from .areadetector.detectors import PCDSAreaDetector
from .epics_motor import IMS
from .inout import CombinedInOutRecordPositioner


class TimeTool(CombinedInOutRecordPositioner):
    """
    TimeTool motion with x- and y-motion motors

    Parameters
    ----------
    prefix : ``str``
        The EPICS base of the TimeTool

    name : ``str``
        A name to refer to the device

    prefix_det : ``str``
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
        super().__init__(prefix, name=name, **kwargs)
        # Assume that having any target in gives transmission 0.8
        self._transmission = {st: 0.8 for st in self.in_states}


class TimeToolWithNav(TimeTool):
    """
    TimeTool motion with zoom, focus, and x- & y-motion motors

    Parameters
    ----------
    prefix : ``str``
        The EPICS base of the TimeTool

    name : ``str``
        A name to refer to the device

    prefix_det : ``str``
        The EPICS base PV of the detector.

    prefix_zoom : ``str``
        The EPICS base PV of the zoom motor.

    prefix_focus : ``str``
        The EPICS base PV of the focus motor
    """
    zoom_motor = FCpt(IMS, '{self._prefix_zoom}', kind='normal')
    focus_motor = FCpt(IMS, '{self._prefix_focus}', kind='normal')

    def __init__(self, prefix, *, name, prefix_zoom, prefix_focus,
                 **kwargs):
        self._prefix_zoom = prefix_zoom
        self._prefix_focus = prefix_focus
        super().__init__(prefix, name=name, **kwargs)
