"""
Module for the `PIM` profile intensity monitor classes
"""
import logging

from ophyd.device import Device, Component as Cpt, FormattedComponent as FCpt
from ophyd.signal import EpicsSignal

from .epics_motor import IMS
from .areadetector.detectors import PCDSAreaDetector
from .inout import InOutRecordPositioner

logger = logging.getLogger(__name__)


class PIM_Y(InOutRecordPositioner):
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
        """
        Save the original position to be restored on `unstage`.
        """
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
    y_motor = Cpt(PIM_Y, '', kind='normal')
    zoom_motor = FCpt(IMS, '{self._prefix_zoom}', kind='normal')
    detector = FCpt(PCDSAreaDetector, '{self._prefix_det}', kind='normal')

    tab_whitelist = ['y_motor', 'zoom_motor', 'detector']

    def infer_prefix(self, prefix):
        if not self._area:
            self._area = prefix.split(':')[0]
            self._section = prefix.split(':')[1]

    @property
    def prefix_start(self):
        return '{0}:{1}:'.format(self._area, self._section)

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

    def __init__(self, prefix, *, name, prefix_det=None, prefix_zoom=None,
                 prefix_focus=None, **kwargs):
        self.infer_prefix(prefix)

        # Infer the focus motor PV from the base prefix
        if prefix_focus:
            self._prefix_focus = prefix_focus
        else:
            self._prefix_focus = self.prefix_start+'CLF:01'

        self.__init__(prefix, name=name, prefix_det=prefix_det,
                      prefix_zoom=prefix_zoom, **kwargs)


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

    def __init__(self, prefix, *, name, prefix_det=None, prefix_zoom=None,
                 prefix_led=None, **kwargs):
        self.infer_prefix(prefix)

        # Infer the illuminator PV from the base prefix
        if prefix_led:
            self._prefix_led = prefix_led
        else:
            self._prefix_led = self.prefix_start+'CIL:01'

        self.__init__(prefix, name=name, prefix_det=prefix_det,
                      prefix_zoom=prefix_zoom, **kwargs)


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
        The EPICS base PV of the detector. If None, it will be attemptted to be
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
