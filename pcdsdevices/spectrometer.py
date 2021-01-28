"""
Module for the various spectrometers.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface, LightpathMixin
from .signal import InternalSignal, PytmcSignal


class Kmono(BaseInterface, Device, LightpathMixin):
    """
    K-edge Monochromator: Used for Undulator tuning and other experiments.

    This device has 3 main members: the crystal (xtal), the reticle
    (ret), and the diode (diode).

    The crystal angle motion has a pitch of 1000:1 HD of 0.6 mm. The crystal
    angle motor has 1000 steps. The crystal vertical motor moves the in and
    out of the beam path.

    The reticle horizontal motor allows for adjustments in the +/- x direction.
    The reticle vertical motor moves reticle in and out of the beam path in
    the +/- y direction.

    The diode horizontal motor allows for adjustments in the +/- x direction.
    The diode vertical motor moves reticle in and out of the beam path in
    the +/- y direction.
    """

    tab_component_names = True

    _icon = 'fa.diamond'
    lightpath_cpts = ['xtal_in', 'xtal_out',
                      'ret_in', 'ret_out',
                      'diode_in', 'diode_out']

    xtal_angle = Cpt(BeckhoffAxis, ':XTAL_ANGLE', kind='normal')
    xtal_vert = Cpt(BeckhoffAxis, ':XTAL_VERT', kind='normal')
    ret_horiz = Cpt(BeckhoffAxis, ':RET_HORIZ', kind='normal')
    ret_vert = Cpt(BeckhoffAxis, ':RET_VERT', kind='normal')
    diode_horiz = Cpt(BeckhoffAxis, ':DIODE_HORIZ', kind='normal')
    diode_vert = Cpt(BeckhoffAxis, ':DIODE_VERT', kind='normal')

    xtal_in = Cpt(InternalSignal, value=None, kind='omitted')
    xtal_out = Cpt(InternalSignal, value=None, kind='omitted')
    ret_in = Cpt(InternalSignal, value=None, kind='omitted')
    ret_out = Cpt(InternalSignal, value=None, kind='omitted')
    diode_in = Cpt(InternalSignal, value=None, kind='omitted')
    diode_out = Cpt(InternalSignal, value=None, kind='omitted')

    def _update_if_changed(self, value, signal):
        if value != signal.get():
            signal.put(value, force=True)

    def _update_state(self, inserted, removed, state):
        self._update_if_changed(inserted, getattr(self, state + '_in'))
        self._update_if_changed(removed, getattr(self, state + '_out'))

    @xtal_vert.sub_default
    def _xtal_state(self, *args, value, **kwargs):
        if value is not None:
            inserted = value > 50
            removed = value < 2
            self._update_state(inserted, removed, 'xtal')

    @ret_vert.sub_default
    def _ret_state(self, *args, value, **kwargs):
        if value is not None:
            inserted = value < 0
            removed = not inserted
            self._update_state(inserted, removed, 'ret')

    @diode_vert.sub_default
    def _diode_state(self, *args, value, **kwargs):
        if value is not None:
            inserted = value < 2
            removed = value > 96.5
            self._update_state(inserted, removed, 'diode')

    def _set_lightpath_states(self, lightpath_values):
        xtal_in = lightpath_values[self.xtal_in]['value']
        xtal_out = lightpath_values[self.xtal_out]['value']
        ret_in = lightpath_values[self.ret_in]['value']
        ret_out = lightpath_values[self.ret_out]['value']
        diode_in = lightpath_values[self.diode_in]['value']
        diode_out = lightpath_values[self.diode_out]['value']

        self._inserted = any((xtal_in, ret_in, diode_in))
        self._removed = all((xtal_out, ret_out, diode_out))

        if ret_in:
            self._transmission = 0
        else:
            self._transmission = 1


class VonHamosCrystal(BaseInterface, Device):
    """Pitch, yaw, and translation motors for control of a single crystal."""
    tab_component_names = True

    pitch = Cpt(BeckhoffAxis, ':Pitch', kind='normal')
    yaw = Cpt(BeckhoffAxis, ':Yaw', kind='normal')
    trans = Cpt(BeckhoffAxis, ':Translation', kind='normal')


class VonHamosFE(BaseInterface, Device):
    """
    von Hamos spectrometer with Focus and Energy motors.

    These motors should be run as user stages and have their PVs passed into
    this object as keyword arguments, as labeled.

    Parameters
    ----------
    prefix : str, optional
        von Hamos base PV.

    name : str
        A name to refer to the device.

    prefix_focus : str
        The EPICS base PV of the motor controlling the spectrometer's focus.

    prefix_energy : str
        The EPICS base PV of the motor controlling the spectrometer energy.
    """

    tab_component_names = True

    # Update PVs in IOC and change here to reflect
    f = FCpt(BeckhoffAxis, '{self._prefix_focus}', kind='normal')
    e = FCpt(BeckhoffAxis, '{self._prefix_energy}', kind='normal')

    def __init__(self, *args, name, prefix_focus, prefix_energy, **kwargs):
        self._prefix_focus = prefix_focus
        self._prefix_energy = prefix_energy
        if args:
            super().__init__(args[0], name=name, **kwargs)
        else:
            super().__init__('', name=name, **kwargs)


class VonHamosFER(VonHamosFE):
    """
    von Hamos spectrometer with Focus, Energy, and Rotation motors.

    These motors should be run as user stages and have their PVs passed into
    this object as keyword arguments, as labeled.

    Parameters
    ----------
    prefix : str, optional
        von Hamos base PV.

    name : str
        A name to refer to the device.

    prefix_focus : str
        The EPICS base PV of the motor controlling the spectrometer's focus.

    prefix_energy : str
        The EPICS base PV of the motor controlling the spectrometer energy.

    prefix_rot : str
        The EPICS base PV of the common rotation motor.
    """

    rot = FCpt(BeckhoffAxis, '{self._prefix_rot}', kind='normal')

    def __init__(self, *args, name, prefix_rot, prefix_focus, prefix_energy,
                 **kwargs):
        self._prefix_rot = prefix_rot
        super().__init__(args[0] if args else '',
                         name=name, prefix_focus=prefix_focus,
                         prefix_energy=prefix_energy, **kwargs)


class VonHamos4Crystal(VonHamosFE):
    """
    von Hamos spectrometer with four crystals and focus and energy motors.

    The common motors should be run as user stages and have their PVs passed
    into this object as keyword arguments. The crystal motors should be run
    from a Beckhoff IOC and their PVs will be inferred from the base prefix.

    Parameters
    ----------
    prefix : str
        von Hamos base PV.

    name : str
        A name to refer to the device.

    prefix_focus : str
        The EPICS base PV of the motor controlling the spectrometer's focus.

    prefix_energy : str
        The EPICS base PV of the motor controlling the spectrometer energy.
    """

    c1 = Cpt(VonHamosCrystal, ':1', kind='normal')
    c2 = Cpt(VonHamosCrystal, ':2', kind='normal')
    c3 = Cpt(VonHamosCrystal, ':3', kind='normal')
    c4 = Cpt(VonHamosCrystal, ':4', kind='normal')

    def __init__(self, prefix, *, name, prefix_focus, prefix_energy, **kwargs):
        super().__init__(prefix, name=name, prefix_focus=prefix_focus,
                         prefix_energy=prefix_energy, **kwargs)


class Mono(BaseInterface, Device):
    """
    L2S-I NEH 2.X Monochromator

    Axilon mechatronic desig with LCLS-II Beckhoff motion architecture.

    Parameters:
    -----------
    preifx : str
        Base PV for the monochromator

    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'

    # Motor components: can read/write positions
    m_pi = Cpt(BeckhoffAxis, ':MMS:M_PI', kind='normal',
               doc='mirror pitch [urad]')
    g_pi = Cpt(BeckhoffAxis, ':MMS:G_PI', kind='normal',
               doc='grating pitch [urad]')
    m_h = Cpt(BeckhoffAxis, ':MMS:M_H', kind='normal',
              doc='mirror horizontal [um]')
    g_h = Cpt(BeckhoffAxis, ':MMS:G_H', kind='normal',
              doc='grating horizontal [um]')
    sd_v = Cpt(BeckhoffAxis, ':MMS:SD_V', kind='normal',
               doc='screwdriver vertical (in/out) [um]')
    sd_rot = Cpt(BeckhoffAxis, ':MMS:SD_ROT', kind='normal',
                 doc='screwdriver rotation [urad]')

    # Additional Pytmc components
    # Upstream Encoders for pitch axes - not linked to NC axis in PLC
    m_pi_up_enc = Cpt(PytmcSignal, ':ENC:M_PI:02', io='i', kind='normal',
                      doc='mirror pitch upstream encoder [urad]')
    g_pi_up_enc = Cpt(PytmcSignal, ':ENC:G_PI:02', io='i', kind='normal',
                      doc='grating pitch upstream encoder [urad]')

    # LED PWR
    led_power_1 = Cpt(PytmcSignal, ':LED:01:PWR', io='io', kind='config',
                      doc='LED power supply controls.')
    led_power_2 = Cpt(PytmcSignal, ':LED:02:PWR', io='io', kind='config',
                      doc='LED power supply controls.')
    led_power_3 = Cpt(PytmcSignal, ':LED:03:PWR', io='io', kind='config',
                      doc='LED power supply controls.')

    # Flow switches
    flow_1 = Cpt(PytmcSignal, ':FSW:01', io='i', kind='normal',
                 doc='flow switch 1')
    flow_2 = Cpt(PytmcSignal, ':FSW:02', io='i', kind='normal',
                 doc='flow switch 2')
    pres_1 = Cpt(PytmcSignal, ':P1', io='i', kind='normal',
                 doc='pressure sensor 1')

    # RTDs
    rtd_1 = Cpt(PytmcSignal, ':RTD:01:TEMP', io='i', kind='normal',
                doc='RTD 1 [deg C]')
    rtd_2 = Cpt(PytmcSignal, ':RTD:02:TEMP', io='i', kind='normal',
                doc='RTD 2 [deg C]')
    rtd_3 = Cpt(PytmcSignal, ':RTD:03:TEMP', io='i', kind='normal',
                doc='RTD 3 [deg C]')
    rtd_4 = Cpt(PytmcSignal, ':RTD:04:TEMP', io='i', kind='normal',
                doc='RTD 4 [deg C]')
    rtd_5 = Cpt(PytmcSignal, ':RTD:05:TEMP', io='i', kind='normal',
                doc='RTD 5 [deg C]')
    rtd_6 = Cpt(PytmcSignal, ':RTD:06:TEMP', io='i', kind='normal',
                doc='RTD 6 [deg C]')
    rtd_7 = Cpt(PytmcSignal, ':RTD:07:TEMP', io='i', kind='normal',
                doc='RTD 7 [deg C]')
    rtd_8 = Cpt(PytmcSignal, ':RTD:08:TEMP', io='i', kind='normal',
                doc='RTD 8 [deg C]')
