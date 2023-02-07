"""
Module for the various spectrometers.
"""
from lightpath import LightpathState
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FCpt

from .device import GroupDevice
from .epics_motor import (IMS, BeckhoffAxis, BeckhoffAxisNoOffset,
                          EpicsMotorInterface)
from .interface import BaseInterface, LightpathMixin
from .signal import InternalSignal, PytmcSignal


class Kmono(BaseInterface, GroupDevice, LightpathMixin):
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

    xtal_angle = Cpt(BeckhoffAxisNoOffset, ':XTAL_ANGLE', kind='normal')
    xtal_vert = Cpt(BeckhoffAxisNoOffset, ':XTAL_VERT', kind='normal')
    ret_horiz = Cpt(BeckhoffAxisNoOffset, ':RET_HORIZ', kind='normal')
    ret_vert = Cpt(BeckhoffAxisNoOffset, ':RET_VERT', kind='normal')
    diode_horiz = Cpt(BeckhoffAxisNoOffset, ':DIODE_HORIZ', kind='normal')
    diode_vert = Cpt(BeckhoffAxisNoOffset, ':DIODE_VERT', kind='normal')

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
            inserted = value < -0.5
            removed = not inserted
            self._update_state(inserted, removed, 'ret')

    @diode_vert.sub_default
    def _diode_state(self, *args, value, **kwargs):
        if value is not None:
            inserted = value < 2
            removed = value > 96.5
            self._update_state(inserted, removed, 'diode')

    def calc_lightpath_state(
        self,
        xtal_in: bool,
        xtal_out: bool,
        ret_in: bool,
        ret_out: bool,
        diode_in: bool,
        diode_out: bool
    ) -> LightpathState:
        self._inserted = any((xtal_in, ret_in, diode_in))
        self._removed = all((xtal_out, ret_out, diode_out))

        self._transmission = 0. if ret_in else 1.

        return LightpathState(
            inserted=self._inserted,
            removed=self._removed,
            output={self.output_branches[0]: self._transmission}
        )


class VonHamosCrystal(BaseInterface, GroupDevice):
    """Pitch, yaw, and translation motors for control of a single crystal."""
    tab_component_names = True

    pitch = Cpt(BeckhoffAxisNoOffset, ':Pitch', kind='normal')
    yaw = Cpt(BeckhoffAxisNoOffset, ':Yaw', kind='normal')
    trans = Cpt(BeckhoffAxisNoOffset, ':Translation', kind='normal')


class VonHamosFE(BaseInterface, GroupDevice):
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
    f = FCpt(BeckhoffAxisNoOffset, '{self._prefix_focus}', kind='normal')
    e = FCpt(BeckhoffAxisNoOffset, '{self._prefix_energy}', kind='normal')

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

    rot = FCpt(BeckhoffAxisNoOffset, '{self._prefix_rot}', kind='normal')

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


class Mono(BaseInterface, GroupDevice, LightpathMixin):
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
    m_pi = Cpt(BeckhoffAxisNoOffset, ':MMS:M_PI', kind='normal',
               doc='mirror pitch [urad]')
    g_pi = Cpt(BeckhoffAxisNoOffset, ':MMS:G_PI', kind='normal',
               doc='grating pitch [urad]')
    m_h = Cpt(BeckhoffAxisNoOffset, ':MMS:M_H', kind='normal',
              doc='mirror horizontal [um]')
    g_h = Cpt(BeckhoffAxisNoOffset, ':MMS:G_H', kind='normal',
              doc='grating horizontal [um]')
    sd_v = Cpt(BeckhoffAxisNoOffset, ':MMS:SD_V', kind='normal',
               doc='screwdriver vertical (in/out) [um]')
    sd_rot = Cpt(BeckhoffAxisNoOffset, ':MMS:SD_ROT', kind='normal',
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

    # Lightpath constants
    inserted = True
    removed = False
    transmission = 1
    SUB_STATE = 'state'

    # dummy component, state is always the same
    lightpath_cpts = ['m_pi.user_readback']

    def calc_lightpath_state(self, **kwargs) -> LightpathState:
        return LightpathState(
            inserted=True,
            removed=False,
            output={self.output_branches[0]: 1}
        )


class TMOSpectrometer(BaseInterface, GroupDevice, LightpathMixin):
    """
    TMO Fresnel Photon Spectrometer Motion components class.

    Photon Spectrometer with LCLS-II Beckhoff motion architecture.

    Parameters:
    -----------
    prefix : str
        Base PV for the motion system

    name : str
        Alias for the device
    """
    # UI Representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components: can read/write positions
    lens_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    lens_pitch_up_down = Cpt(BeckhoffAxis, ':MMS:10', kind='normal')
    lens_yaw_left_right = Cpt(BeckhoffAxis, ':MMS:11', kind='normal')
    foil_x = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    zone_plate_x = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')
    zone_plate_y = Cpt(BeckhoffAxis, ':MMS:04', kind='normal')
    zone_plate_z = Cpt(BeckhoffAxis, ':MMS:05', kind='normal')
    yag_x = Cpt(BeckhoffAxis, ':MMS:06', kind='normal')
    yag_y = Cpt(BeckhoffAxis, ':MMS:07', kind='normal')
    yag_z = Cpt(BeckhoffAxis, ':MMS:08', kind='normal')
    yag_theta = Cpt(BeckhoffAxis, ':MMS:09', kind='normal')

    # Lightpath constants
    inserted = True
    removed = False
    transmission = 1
    SUB_STATE = 'state'

    # dummy signal, state is always the same
    lightpath_cpts = ['yag_x.user_readback']

    def calc_lightpath_state(self, **kwargs) -> LightpathState:
        # TODO: get real logic here, instead of legacy hard-coding
        return LightpathState(
            inserted=True,
            removed=False,
            output={self.output_branches[0]: 1}
        )


class HXRSpectrometer(BaseInterface, GroupDevice, LightpathMixin):
    """
    HXR Single Shot Spectrometer motion components class.

    Parameters:
    -----------
    prefix : str
        Base PV for spectrometer motors.

    name : str
        Alias for the device.
    """

    tab_component_names = True

    xtaly = Cpt(IMS, ':441:MOTR', kind='normal',
                doc='crystal y')
    th = Cpt(IMS, ':442:MOTR', kind='normal',
             doc='crystal angle')
    tth = Cpt(IMS, ':443:MOTR', kind='normal',
              doc='camera angle')
    camd = Cpt(IMS, ':444:MOTR', kind='normal',
               doc='camera distance')
    camy = Cpt(IMS, ':447:MOTR', kind='normal',
               doc='camera y')
    iris = Cpt(IMS, ':445:MOTR', kind='normal',
               doc='camera iris')
    filter = Cpt(IMS, ':446:MOTR', kind='normal',
                 doc='filter wheel, tbd if necessary')

    # Lightpath constants
    inserted = True
    removed = False
    transmission = 1
    SUB_STATE = 'state'

    # dummy signal, state is always the same
    lightpath_cpts = ['xtaly.user_readback']

    def calc_lightpath_state(self, **kwargs) -> LightpathState:
        return LightpathState(
            inserted=True,
            removed=False,
            output={self.output_branches[0]: 1}
        )


class Gen1VonHamosCrystal(BaseInterface, GroupDevice):
    """Pitch, yaw, and translation motors for control of a single crystal."""

    tab_component_names = True

    pitch = FCpt(EpicsMotorInterface, '{prefix}{_pitch_axis}', kind='normal')
    yaw = FCpt(EpicsMotorInterface, '{prefix}{_yaw_axis}'  , kind='normal')
    trans = FCpt(EpicsMotorInterface, '{prefix}{_trans_axis}', kind='normal')

    def __init__(self, prefix, pitch_axis, yaw_axis, trans_axis, **kwargs):
        self._pitch_axis = pitch_axis
        self._yaw_axis = yaw_axis
        self._trans_axis = trans_axis
        super().__init__(prefix, **kwargs)


class Gen1VonHamos4Crystal(BaseInterface, GroupDevice):
    """
    Four crystal Von Hamos setup controlled with a Beckhoff PLC.

    This includes three axes for each crystal manipulator, and a common rotation axis.
    Each of their PVs will be inferred from the base prefix.

    Parameters
    ----------
    prefix : str, optional
        Von Hamos base PV.

    name : str
        A name to refer to the device.
    """

    tab_component_names = True

    common_yaw = Cpt(EpicsMotorInterface, ':01', kind='normal', name='Common Rotation')

    cr1 = Cpt(Gen1VonHamosCrystal, '', trans_axis=':02', yaw_axis=':06', pitch_axis=':10' , kind='normal', name='Crystal 1')
    cr2 = Cpt(Gen1VonHamosCrystal, '', trans_axis=':03', yaw_axis=':07', pitch_axis=':11' , kind='normal', name='Crystal 2')
    cr3 = Cpt(Gen1VonHamosCrystal, '', trans_axis=':04', yaw_axis=':08', pitch_axis=':12' , kind='normal', name='Crystal 3')
    cr4 = Cpt(Gen1VonHamosCrystal, '', trans_axis=':05', yaw_axis=':09', pitch_axis=':13' , kind='normal', name='Crystal 4')
