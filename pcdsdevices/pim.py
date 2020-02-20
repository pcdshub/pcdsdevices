"""
Profile Intensity Monitor Classes

This module contains all the classes relating to the profile intensity monitor
classes at the user level. A PIM will usually have at least a motor to control
yag position and a camera to view the yag.
"""
import logging

from ophyd.device import Device, Component as Cpt, FormattedComponent as FCpt
from ophyd.signal import EpicsSignal

from .areadetector.detectors import PCDSAreaDetector
from .epics_motor import BeckhoffAxis
from .inout import InOutRecordPositioner, TwinCATInOutPositioner
from .interface import BaseInterface
from .sensors import TwinCATThermoCouple
from .signal import PytmcSignal
from .state import StatePositioner

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


class LCLS2ImagerBase(Device, BaseInterface):
    """
    Shared PVs and components from the LCLS2 imagers

    All LCLS2 imagers are guaranteed to have the following components that
    behave essentially the same
    """
    tab_component_names = True

    y_states = Cpt(TwinCATInOutPositioner, ':STATE', kind='hinted')
    y_motor = Cpt(BeckhoffAxis, ':MMS', kind='normal')
    detector = Cpt(PCDSAreaDetector, ':CAM:', kind='normal')
    cam_power = Cpt(PytmcSignal, ':CAM:PWR', io='io', kind='config')


class PPMPowerMeter(Device, BaseInterface):
    """
    Analog measurement tool for beam energy as part of the PPM assembly.

    When inserted into the beam, the ``raw_voltage`` signal value should
    increase proportional to the beam energy. The equivalent calibrated
    readings are ``dimensionless``, which is a unitless number that
    represents the relative calibration of every power meter, and
    ``calibrated_mj``, which is the real engineering unit of the beam
    power. These are calibrated using the other signals in the following way:

    ``dimensionless`` = (``raw_voltage`` + ``calib_offset``) * ``calib_ratio``
    ``calibrated_mj`` = ``dimensionless`` * ``calib_mj_ratio``
    """
    tab_component_names = True

    raw_voltage = Cpt(PytmcSignal, ':VOLT', io='i', kind='normal')
    dimensionless = Cpt(PytmcSignal, ':CALIB', io='i', kind='normal')
    calibrated_mj = Cpt(PytmcSignal, ':MJ', io='i', kind='normal')
    thermocouple = Cpt(TwinCATThermoCouple, '', kind='normal')

    calib_offset = Cpt(PytmcSignal, ':CALIB:OFFSET', io='io', kind='config')
    calib_ratio = Cpt(PytmcSignal, ':CALIB:RATIO', io='io', kind='config')
    calib_mj_ratio = Cpt(PytmcSignal, ':CALIB:MJ_RATIO', io='io', kind='config')

    raw_voltage_buffer = Cpt(PytmcSignal, ':VOLT_BUFFER', io='i',
                             kind='omitted')
    dimensionless_buffer = Cpt(PytmcSignal, ':CALIB_BUFFER', io='i',
                               kind='omitted')
    calibrated_mj_buffer = Cpt(PytmcSignal, ':MJ_BUFFER', io='i',
                               kind='omitted')


class PPM(LCLS2ImagerBase):
    """
    L2SI's Power and Profile Monitor design.

    Unlike the `XPIM`, this includes a power meter and two thermocouples, one
    on the power meter itself and one on the yag holder. The LED on this unit
    has been outfitted with a dimmable control in units of percentage.

    Parameters
    ----------
    prefix: ``str``
        The EPICS PV prefix for this imager, e.g. ``IM3L0:PPM``.

    name: ``str``, required keyword
        An identifying name for this motor, e.g. ``im3l0``
    """
    power_meter = Cpt(PPMPowerMeter, ':SPM', kind='normal')
    yag_thermocouple = Cpt(TwinCATThermoCouple, ':YAG', kind='normal')

    led = Cpt(PytmcSignal, ':CAM:CIL:PCT', io='io', kind='config')


class XPIMFilterWheel(StatePositioner):
    """
    Controllable optical filters to prevent camera saturation.

    There are six filter slots, five with filters of varying optical densities
    and one that is empty. The enum strings here are T100, T50, etc. which
    represent the transmission percentage of the associated filter.
    """
    tab_component_names = True

    state = Cpt(EpicsSignal, ':GET_RBV', write_pv='SET', kind='normal')

    reset_cmd = Cpt(PytmcSignal, ':ERR:RESET', io='i', kind='omitted')
    error_message = Cpt(PytmcSignal, ':ERR:MSG', io='i', kind='omitted')


class XPIM(LCLS2ImagerBase):
    """
    XTES's Imager design.

    Unlike the `PPM`, this includes a relative encoder zoom and focus dc motor
    stack and a controllable optical filter wheel. The LED on this unit has
    only been outfitted with binary control, on/off.

    Parameters
    ----------
    prefix: ``str``
        The EPICS PV prefix for this imager, e.g. ``IM3L0:PPM``.

    name: ``str``, required keyword
        An identifying name for this motor, e.g. ``im3l0``
    """
    zoom_motor = Cpt(BeckhoffAxis, ':CLZ', kind='normal')
    focus_motor = Cpt(BeckhoffAxis, ':CLF', kind='normal')

    led = Cpt(PytmcSignal, ':CAM:CIL:PWR', io='io', kind='config')
    filter_wheel = Cpt(XPIMFilterWheel, ':MFW', kind='config')
