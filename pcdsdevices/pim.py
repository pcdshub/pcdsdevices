"""
Module for the `PIM` Profile Intensity Monitor classes.

This module contains all the classes relating to the profile intensity monitor
classes at the user level. A PIM always has a motor to control yag/diode
position, a zoom motor, and a camera to view the yag. Some PIMs have LEDs for
illumination and/or a focus motor. Each of these configurations is set up as
its own class.
"""
import logging

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.ophydobj import OphydObject
from ophyd.signal import EpicsSignal

from .analog_signals import FDQ
from .areadetector.detectors import (PCDSAreaDetectorEmbedded,
                                     PCDSAreaDetectorTyphosTrigger)
from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .digital_signals import J120K
from .epics_motor import IMS, BeckhoffAxisNoOffset
from .inout import InOutRecordPositioner
from .interface import BaseInterface, LightpathInOutCptMixin
from .keithley import IM3L0_K2700
from .pmps import TwinCATStatePMPS
from .sensors import TwinCATThermocouple
from .signal import PytmcSignal, UnitConversionDerivedSignal
from .state import StatePositioner
from .utils import get_status_float, get_status_value, reorder_components
from .variety import set_metadata

logger = logging.getLogger(__name__)


class PIMY(InOutRecordPositioner, BaseInterface):
    """
    Standard Y-motor for a Profile Intensity Monitor.

    This can move the stage to insert the YAG or diode, or retract from the
    beam path.
    """

    # Automatically discover states (not all PIMs have DIODE)
    states_list = []
    _in_if_not_out = True

    _states_alias = {'YAG': 'IN'}
    # QIcon for UX
    _icon = 'fa.camera-retro'

    tab_whitelist = ['stage']
    _pre_stage_state = None

    def stage(self) -> list[OphydObject]:
        """Save the original position to be restored on `unstage`."""
        self._pre_stage_state = self.state.get()
        return super().stage()

    def unstage(self) -> list[OphydObject]:
        """Load the original position that was saved on `stage`."""
        if self._pre_stage_state is not None:
            self.state.put(self._pre_stage_state)
        self._pre_stage_state = None
        return super().unstage()


class PIM(BaseInterface, GroupDevice, LightpathInOutCptMixin):
    """
    Profile Intensity Monitor.

    Consists of y-motion and zoom motors, and an area detector.

    Parameters
    ----------
    prefix : str
        The EPICS base of the PIM.

    name : str
        A name to refer to the device.

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be attempted to be
        inferred from `prefix`.

    prefix_zoom : str, optional
        The EPICS base PV of the zoom motor. If None, it will be attempted to
        be inferred from `prefix`.
    """

    _prefix_start = ''

    state = Cpt(PIMY, '', kind='normal')
    zoom = FCpt(IMS, '{self._prefix_zoom}', kind='normal')
    detector = FCpt(PCDSAreaDetectorEmbedded, '{self._prefix_det}',
                    kind='normal')

    tab_whitelist = ['y', 'remove', 'insert', 'removed', 'inserted']
    tab_component_names = True

    lightpath_cpts = ['state']

    def infer_prefix(self, prefix):
        """Pulls out the first two segments of the prefix PV, if not already
           done"""
        if not self._prefix_start:
            self._prefix_start = '{}:{}:'.format(
                prefix.split(':')[0],
                prefix.split(':')[1],
            )

    def format_status_info(self, status_info):
        """
        Override status info handler to render the PIM.

        Display pim status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.
        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        focus = get_status_value(status_info, 'focus', 'position')
        f_units = get_status_value(status_info, 'focus', 'user_setpoint',
                                   'units')
        state_pos = get_status_value(status_info, 'state', 'position')
        y_pos = get_status_float(status_info, 'state', 'motor', 'position',
                                 precision=4)
        y_units = get_status_value(status_info, 'state', 'motor',
                                   'user_setpoint', 'units')
        zoom = get_status_float(status_info, 'zoom', 'position',
                                precision=4)
        z_units = get_status_value(status_info, 'zoom', 'user_setpoint',
                                   'units')

        name = ' '.join(self.prefix.split(':'))
        if focus != 'N/A':
            focus = f' Focus: {focus} [{f_units}]'
        else:
            focus = ''
        if zoom != 'N/A':
            zoom = f'Navitar Zoom: {zoom} [{z_units}]'
        else:
            zoom = ''

        return f"""\
{name}: {state_pos}
Y Position: {y_pos} [{y_units}]
{zoom}{focus}
"""

    @property
    def prefix_start(self):
        """Returns the first two segments of the prefix PV."""
        return str(self._prefix_start)

    @property
    def removed(self):
        """Returns `True` if the yag and diode are removed from the beam."""
        return self.state.removed

    @property
    def inserted(self):
        """Returns `True` if yag or diode are inserted."""
        return self.state.inserted

    def insert(self, moved_cb=None, timeout=None, wait=False):
        """Moves the YAG into the beam."""
        return self.state.insert(moved_cb=moved_cb, timeout=timeout,
                                 wait=wait)

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """Moves the YAG and diode out of the beam."""
        return self.state.remove(moved_cb=moved_cb, timeout=timeout,
                                 wait=wait)

    def __init__(self, prefix, *, name, prefix_det=None, prefix_zoom=None,
                 **kwargs):
        self.infer_prefix(prefix)

        # Infer the detector PV from the base prefix
        if prefix_det:
            self._prefix_det = prefix_det
        else:
            self._prefix_det = self.prefix_start+'CVV:01:'

        # Infer the zoom motor PV from the base prefix
        if prefix_zoom:
            self._prefix_zoom = prefix_zoom
        else:
            self._prefix_zoom = self.prefix_start+'CLZ:01'

        super().__init__(prefix, name=name, **kwargs)
        self.y = self.state.motor


class PIMWithFocus(PIM):
    """
    Profile Intensity Monitor with Focus control.

    Consists of y-motion, zoom, and focus motors, and an area detector.

    Parameters
    ----------
    prefix : str
        The EPICS base of the PIM.

    name : str
        A name to refer to the device.

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be attempted to be
        inferred from `prefix`.

    prefix_zoom : str, optional
        The EPICS base PV of the zoom motor. If None, it will be attempted to
        be inferred from `prefix`.

    prefix_focus : str, optional
        The EPICS base PV of the focus motor. If None, it will be attempted to
        be inferred from `prefix`.
    """

    focus = FCpt(IMS, '{self._prefix_focus}', kind='normal')

    def __init__(self, prefix, *, name, prefix_focus=None, **kwargs):
        self.infer_prefix(prefix)

        # Infer the focus motor PV from the base prefix
        if prefix_focus:
            self._prefix_focus = prefix_focus
        else:
            self._prefix_focus = self.prefix_start+'CLF:01'

        super().__init__(prefix, name=name, **kwargs)


class PIMWithLED(PIM):
    """
    Profile Intensity Monitor with LED.

    Consists of a y-motion motor, zoom motor, LED, and an area detector.

    Parameters
    ----------
    prefix : str
        The EPICS base of the PIM.

    name : str
        A name to refer to the device.

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be attempted to be
        inferred from `prefix`.

    prefix_zoom : str, optional
        The EPICS base PV of the zoom motor. If None, it will be attempted to
        be inferred from `prefix`.

    prefix_led : str, optional
        The EPICS base PV of the LED. If None, it will be attempted to be
        inferred from `prefix`.
    """
    led = FCpt(EpicsSignal, '{self._prefix_led}', kind='normal')

    def __init__(self, prefix, *, name, prefix_led=None, **kwargs):
        self.infer_prefix(prefix)

        # Infer the illuminator PV from the base prefix
        if prefix_led:
            self._prefix_led = prefix_led
        else:
            self._prefix_led = self.prefix_start+'CIL:01'

        super().__init__(prefix, name=name, **kwargs)


class PIMWithBoth(PIMWithFocus, PIMWithLED):
    """
    Profile Intensity Monitor with LED and Focus control.

    Consists of a y-motion motor, zoom motor, focus motor, LED, and an area
    detector.

    Parameters
    ----------
    prefix : str
        The EPICS base of the PIM.

    name : str
        A name to refer to the device.

    prefix_det : str, optional
        The EPICS base PV of the detector. If None, it will be attempted to be
        inferred from `prefix`.

    prefix_zoom : str, optional
        The EPICS base PV of the zoom motor. If None, it will be attempted to
        be inferred from `prefix`.

    prefix_focus : str, optional
        The EPICS base PV of the focus motor. If None, it will be attempted to
        be inferred from `prefix`.

    prefix_led : str, optional
        The EPICS base PV of the LED. If None, it will be attempted to be
        inferred from `prefix`.
    """

    def __init__(self, prefix, *, name, prefix_focus=None, prefix_led=None,
                 prefix_det=None, prefix_zoom=None, **kwargs):
        super().__init__(prefix, name=name, prefix_focus=prefix_focus,
                         prefix_led=prefix_led, prefix_det=prefix_det,
                         prefix_zoom=prefix_zoom, **kwargs)


class LCLS2Target(TwinCATStatePMPS):
    """
    Controls the PPM and XTES Imager states.

    Defines the state count as 4 (OUT and 3 targets) to limit the number of
    config PVs we connect to.

    The PPM and the XTES Imager have the same state count,
    despite having different targets at those states.
    """
    config = UpCpt(state_count=4)


class LCLS2ImagerBase(BaseInterface, GroupDevice, LightpathInOutCptMixin):
    """
    Shared PVs and components from the LCLS2 imagers.

    All LCLS2 imagers are guaranteed to have the following components that
    behave essentially the same.
    """
    tab_component_names = True

    lightpath_cpts = ['target']
    _icon = 'fa.video-camera'

    target = Cpt(LCLS2Target, ':MMS:STATE', kind='hinted',
                 doc='Control of the diagnostic stack via saved positions.')
    y_motor = Cpt(BeckhoffAxisNoOffset, ':MMS', kind='normal',
                  doc='Direct control of the diagnostic stack motor.')
    detector = Cpt(PCDSAreaDetectorTyphosTrigger, ':CAM:', kind='normal',
                   doc='Area detector settings and readbacks.')
    cam_power = Cpt(PytmcSignal, ':CAM:PWR', io='io', kind='config',
                    doc='Camera power supply controls.')
    set_metadata(cam_power, dict(variety='command-enum'))

    @property
    def y_states(self):
        """Alias old name. Will deprecate."""
        return self.target


class PPMPowerMeter(BaseInterface, Device):
    """
    Analog measurement tool for beam energy as part of the PPM assembly.

    When inserted into the beam, the `raw_voltage` signal value should
    increase proportional to the beam energy. A responsivity value
    calibrated for each power meter in units of volts per watt
    is used to calculate the actual energy in the following way:

    `calibrated_mj` = (Signal - Background) / (Responsivity * Beam_Rate)
    """

    tab_component_names = True

    responsivity = Cpt(PytmcSignal, ':RESP', io='i', kind='normal',
                       doc='Responsivity in  V/W, unique for every power meter.')

    background_voltage = Cpt(PytmcSignal, ':BACK:VOLT', io='io', kind='normal',
                             doc='Background voltage value used to calculate pulse energy.')

    auto_background_reset = Cpt(PytmcSignal, ':BACK:RESET', io='io', kind='normal',
                                doc='Set to reset auto background voltage collection.')
    set_metadata(auto_background_reset, dict(variety='command-proc', value=1))

    background_mode = Cpt(PytmcSignal, ':BACK:MODE', io='io', kind='normal',
                          doc='Can be manual or auto In manual mode, you can collect '
                          'for a specified number of seconds. In auto mode, a buffer of '
                          'automatically collected background voltages will be used to calculate the background voltage.')

    manual_collect = Cpt(PytmcSignal, ':BACK:COLL', io='io', kind='normal',
                         doc='Start collecting background voltages for specified time.')
    set_metadata(manual_collect, dict(variety='command-proc', value=1))

    manual_in_progress = Cpt(PytmcSignal, ':BACK:MANUAL_COLLECTING', io='i', kind='normal',
                             doc='Manual collection currntly in progress')
    set_metadata(manual_in_progress, dict(variety='command'))

    manual_collect_time = Cpt(PytmcSignal, ':BACK:TIME', io='io', kind='normal',
                              doc='Time to collect background voltages for.')

    raw_voltage = Cpt(PytmcSignal, ':VOLT', io='i', kind='normal',
                      doc='Raw readback from the power meter.')

    calibrated_mj = Cpt(PytmcSignal, ':MJ', io='i', kind='normal',
                        doc='Calibrated absolute measurement of beam '
                            'power in physics units.')

    calibrated_uj = Cpt(UnitConversionDerivedSignal, derived_from='calibrated_mj',
                        derived_units='uJ', original_units='mJ', write_access=False)

    wattage = Cpt(PytmcSignal, ':WATT', io='i', kind='normal',
                  doc='Wattage measured by power meter, equals MJ times Beamrate.')

    thermocouple = Cpt(TwinCATThermocouple, '', kind='normal',
                       doc='Thermocouple on the power meter holder.')

    raw_voltage_buffer = Cpt(PytmcSignal, ':VOLT_BUFFER', io='i',
                             kind='omitted',
                             doc='Array of the last 1000 raw measurements. '
                                 'Polls faster than the EPICS updates.')

    calibrated_mj_buffer = Cpt(PytmcSignal, ':MJ_BUFFER', io='i',
                               kind='omitted',
                               doc='Array of the last 1000 fully calibrated '
                                   'measurements. Polls faster than the '
                                   'EPICS updates.')

    wattage_buffer = Cpt(PytmcSignal, ':WATT_BUFFER', io='i',
                         kind='omitted',
                         doc='Array of the last 1000 wattages. Polls faster than the '
                         'EPICS updates.')


class PPM(LCLS2ImagerBase):
    """
    L2SI's Power and Profile Monitor design.

    Unlike the `XPIM`, this includes a power meter and two thermocouples, one
    on the power meter itself and one on the yag holder. The LED on this unit
    has been outfitted with a dimmable control in units of percentage.

    Parameters
    ----------
    prefix : str
        The EPICS PV prefix for this imager, e.g. 'IM3L0:PPM'.

    name : str
        An identifying name for this motor, e.g. 'im3l0'.
    """

    power_meter = Cpt(PPMPowerMeter, ':SPM', kind='normal',
                      doc='Device that measures power of incident beam.')
    yag_thermocouple = Cpt(TwinCATThermocouple, ':YAG', kind='normal',
                           doc='Thermocouple on the YAG holder.')

    led = Cpt(PytmcSignal, ':CAM:CIL:PCT', io='io', kind='config',
              doc='Percent of light from the dimmable illuminatior.')
    set_metadata(led, dict(variety='scalar-range',
                           range={'value': (0, 100),
                                  'source': 'value'}
                           ))


class XPIMFilterWheel(StatePositioner):
    """
    Controllable optical filters to prevent camera saturation.

    There are six filter slots, five with filters of varying optical densities
    and one that is empty. The enum strings here are T100, T50, etc. which
    represent the transmission percentage of the associated filter.
    """

    tab_component_names = True

    state = Cpt(EpicsSignal, ':GET_RBV', write_pv=':SET', kind='normal',
                doc='Control of the filter wheel state by preset '
                    'transmission percentages.')

    reset_cmd = Cpt(PytmcSignal, ':ERR:RESET', io='i', kind='omitted',
                    doc='Command to reset a filter wheel error.')
    error_message = Cpt(PytmcSignal, ':ERR:MSG', io='i', kind='omitted',
                        string=True,
                        doc='Error text for a filter wheel error.')

    set_metadata(state, dict(variety='command-enum'))


class XPIMLED(BaseInterface, Device):
    """
    Controllable illumination with auto-on, auto-off, and shutdown timer.

    The power signal will read back the current LED power state, and can be
    used to set the power state if we are not in auto_mode.

    The power_timeout signal can be used to configure the LED shutdown in
    units of minutes. If power_timeout is zero, there will not be a timeout
    and the LED is permitted to stay on indefinitely.

    The time_remaining signal is the number of minutes remaining until the
    power timeout elapses. This can be put to if the user wants to stall the
    timer without reconfiguring the timeout.

    The auto_mode signal switches us between automatic and manual modes. In
    automatic mode, we'll turn the LED on when in the reticle state and off
    when leaving the reticle state. This is the only time when the LED is
    useful. Disable this if the state configuration is wrong.
    """

    tab_component_names = True

    power = Cpt(PytmcSignal, ':PWR', io='io', kind='normal',
                doc='LED power state, either on or off.')
    power_timeout = Cpt(PytmcSignal, ':CLK:TIMEOUT', io='io', kind='config',
                        doc='Configured auto-shutdown timeout for the led.')
    time_remaining = Cpt(PytmcSignal, ':CLK:REMAINING', io='io', kind='config',
                         doc='Remaining time before auto-shutoff.')
    auto_mode = Cpt(PytmcSignal, ':AUTO', io='io', kind='config',
                    doc='Configure auto mode vs manual mode for turning '
                        'the LED on and off.')

    set_metadata(power, dict(variety='command-enum'))
    set_metadata(auto_mode, dict(variety='command-enum'))


class XPIM(LCLS2ImagerBase):
    """
    XTES's Imager design.

    Unlike the `PPM`, this includes a relative encoder zoom and focus dc motor
    stack and a controllable optical filter wheel. The LED on this unit has
    only been outfitted with binary control, on/off.

    Parameters
    ----------
    prefix : str
        The EPICS PV prefix for this imager, e.g. 'IM3L0:PPM'.

    name : str
        An identifying name for this motor, e.g. 'im3l0'.
    """

    zoom_motor = Cpt(BeckhoffAxisNoOffset, ':CLZ', kind='normal',
                     doc='Motorized zoom.')
    focus_motor = Cpt(BeckhoffAxisNoOffset, ':CLF', kind='normal',
                      doc='Motorized focus.')

    zoom_lock = Cpt(PytmcSignal, ':CLZ:LOCK', io='io', kind='config',
                    doc='Lockout to prevent zoom motion.')
    focus_lock = Cpt(PytmcSignal, ':CLF:LOCK', io='io', kind='config',
                     doc='Lockout to prevent focus motion.')
    led = Cpt(XPIMLED, ':CIL', kind='config',
              doc='LED for viewing the reticle.')
    filter_wheel = Cpt(XPIMFilterWheel, ':MFW', kind='config',
                       doc='Optical filter wheel in front of the camera '
                           'to prevent saturation.')
    flow_switch = Cpt(J120K, '', kind='normal',
                      doc='Device that indicates nominal PCW Flow Rate.')

    set_metadata(zoom_lock, dict(variety='command-enum'))
    set_metadata(focus_lock, dict(variety='command-enum'))


class IM2K0(LCLS2ImagerBase):
    """
    One-off combination of an XPIM and a PPM for scientific merit.

    This is primarily an XPIM, but the lens/camera/illuminator are swapped for
    the PPM models. Somehow this makes it the least complicated imager on the
    beamline.
    """
    # XPIM illuminator
    led = Cpt(XPIMLED, ':CIL', kind='config',
              doc='LED for viewing the reticle.')
    flow_switch = Cpt(J120K, '', kind='normal',
                      doc='Device that indicates nominal PCW Flow Rate.')
    # Nothing else! No power meter, no zoom/focus, no filter wheel...


@reorder_components(
    end_with=['k2700', 'power_meter', 'yag_thermocouple', 'led']
)
class IM3L0(PPM):
    """
    One-off subclass of PPM to include this device's Keithley 2700

    Includes a Keithley 2700 digital multimeter on top of the PPM class, mainly
    so it shows up on this device's detailed screen.
    """
    k2700 = Cpt(IM3L0_K2700, ':SPM:K2700',
                doc='Digital multimeter to get power readouts for this device.')


class PPMCOOL(PPM):
    """
    L2SI's Power and Profile Monitor design with cooling.
    """
    flow_meter = Cpt(FDQ, '', kind='normal',
                     doc='Device that measures PCW Flow Rate.')


class PPMCoolSwitch(PPM):
    """
    L2SI's Power and Profile Monitor design with cooling switch.
    """
    flow_switch = Cpt(J120K, '', kind='normal',
                      doc='Device that indicates nominal PCW Flow Rate.')
