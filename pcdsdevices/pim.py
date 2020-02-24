"""
Module for the `PIM` profile intensity monitor classes

This module contains all the classes relating to the profile intensity monitor
classes at the user level. A PIM always has a motor to control yag/diode 
position, a zoom motor, and a camera to view the yag. Some PIMs have LEDs for
illumination and/or a focus motor. Each of these configurations is set up as
its own class.
"""
import logging

from ophyd.device import Device, Component as Cpt, FormattedComponent as FCpt
from ophyd.signal import EpicsSignal

from .epics_motor import IMS
from .areadetector.detectors import PCDSAreaDetector
from .inout import InOutRecordPositioner

logger = logging.getLogger(__name__)


class PIMY(InOutRecordPositioner):
    """
    Standard profile monitor Y motor.

    This can move the stage to insert the yag
    or diode, or retract from the beam path.
    """
    states_list = ['DIODE', 'YAG', 'OUT']
    in_states = ['YAG', 'DIODE']

    _states_alias = {'YAG': 'IN'}
    # QIcon for UX
    _icon = 'fa.camera-retro'

    def stage(self):
        """Save the original position to be restored on `unstage`."""
        self._original_vals[self.state] = self.state.value
        return super().stage()


class PIM(Device):
    """
    Profile intensity monitor with y-motion motor, zoom motor, and a detector.

    Parameters
    ----------
    prefix : str
        The EPICS base of the PIM

    name : str
        A name to refer to the device

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be attemptted to be
        inferred from `prefix`

    prefix_zoom : str, optional
        The EPICS base PV of the zoom motor. If None, it will be attempted to
        be inferred from `prefix`
    """

    _prefix_start = ''

    state = Cpt(PIM_Y, '', kind='normal')
    zoom_motor = FCpt(IMS, '{self._prefix_zoom}', kind='normal')
    detector = FCpt(PCDSAreaDetector, '{self._prefix_det}', kind='normal')

    tab_whitelist = ['y_motor', 'zoom_motor', 'detector']

    def infer_prefix(self, prefix):
        """Pulls out the first two segments of the prefix PV, if not already
           done"""
        if not self._prefix_start:
            self._prefix_start = '{0}:{1}:'.format(prefix.split(':')[0],
                                                   prefix.split(':')[1])

    @property
    def prefix_start(self):
        """Returns the first two segments of the prefix PV."""
        return str(self._prefix_start)

    @property
    def removed(self):
        """Returns ``True`` if the yag and diode are removed from the beam."""
        return self.state.removed

    @property
    def inserted(self):
        """Returns ``True`` if yag or diode are inserted."""
        return self.state.inserted

    def insert(self, moved_cb=None, timeout=None, wait=False):
        """Moves the diode into the beam."""
        return self.state.insert(moved_cb=moved_cb, timeout=timeout,
                                 wait=wait)

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """Moves the diode out of the beam."""
        return self.state.remove(moved_cb=moved_cb, timeout=timeout,
                                 wait=wait)

    def __init__(self, prefix, *, name, prefix_det=None, prefix_zoom=None,
                 **kwargs):
        self.infer_prefix(prefix)

        # Infer the detector PV from the base prefix
        if prefix_det:
            self._prefix_det = prefix_det
        else:
            self._prefix_det = self.prefix_start+'CVV:01'

        # Infer the zoom motor PV from the base prefix
        if prefix_zoom:
            self._prefix_zoom = prefix_zoom
        else:
            self._prefix_zoom = self.prefix_start+'CLZ:01'

        super().__init__(prefix, name=name, **kwargs)
        self.y_motor = self.state.motor


class PIM_withFocus(PIM):
    """
    Profile intensity monitor with y-motion motor, zoom motor, focus motor, and
    a detector.

    Parameters
    ----------
    prefix : str
        The EPICS base of the PIM

    name : str
        A name to refer to the device

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be attemptted to be
        inferred from `prefix`

    prefix_zoom : str, optional
        The EPICS base PV of the zoom motor. If None, it will be attempted to
        be inferred from `prefix`

    prefix_focus : str, optional
        The EPICS base PV of the focus motor. If None, it will be attempted to
        be inferred from `prefix`
    """
    focus_motor = FCpt(IMS, '{self._prefix_focus}')

    def __init__(self, prefix, *, name, prefix_focus=None, **kwargs):
        self.infer_prefix(prefix)

        # Infer the focus motor PV from the base prefix
        if prefix_focus:
            self._prefix_focus = prefix_focus
        else:
            self._prefix_focus = self.prefix_start+'CLF:01'

        super().__init__(prefix, name=name, **kwargs)


class PIM_withLED(PIM):
    """
    Profile intensity monitor with y-motion motor, zoom motor, LED, and a
    detector.

    Parameters
    ----------
    prefix : str
        The EPICS base of the PIM

    name : str
        A name to refer to the device

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be attemptted to be
        inferred from `prefix`

    prefix_zoom : str, optional
        The EPICS base PV of the zoom motor. If None, it will be attempted to
        be inferred from `prefix`

    prefix_led : str, optional
        The EPICS base PV of the LED. If None, it will be attempted to be
        inferred from `prefix`
    """
    led = FCpt(EpicsSignal, '{self._prefix_led}')

    def __init__(self, prefix, *, name, prefix_led=None, **kwargs):
        self.infer_prefix(prefix)

        # Infer the illuminator PV from the base prefix
        if prefix_led:
            self._prefix_led = prefix_led
        else:
            self._prefix_led = self.prefix_start+'CIL:01'

        super().__init__(prefix, name=name, **kwargs)


class PIM_withBoth(PIM_withLED, PIM_withFocus):
    """
    Profile intensity monitor with y-motion motor, zoom motor, focus motor,
    LED, and a detector.

    Parameters
    ----------
    prefix : str
        The EPICS base of the PIM

    name : str
        A name to refer to the device

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be attempted to be
        inferred from `prefix`

    prefix_zoom : str, optional
        The EPICS base PV of the zoom motor. If None, it will be attempted to
        be inferred from `prefix`

    prefix_focus : str, optional
        The EPICS base PV of the focus motor. If None, it will be attempted to
        be inferred from `prefix`

    prefix_led : str, optional
        The EPICS base PV of the LED. If None, it will be attempted to be
        inferred from `prefix`
    """
    pass
