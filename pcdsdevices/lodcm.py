"""
LODCM: Large offset dual-crystal monochrometer.

The scope of this module is to identify where the beam is intended to go after
passing through H1N, to manipulate the diagnostics, and to remove H1N for the
downstream hutches.

It will not be possible to align the device with the class, and there will be
no readback into the device's alignment. This is intended for a future update.
"""
import functools
import logging

import numpy as np
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.device import FormattedComponent as FCpt
from ophyd.signal import EpicsSignalRO
from ophyd.sim import NullStatus
from ophyd.status import wait as status_wait
from pcdscalc import common, diffraction

from pcdsdevices.epics_motor import OffsetMotor, OffsetIMSWithPreset
from pcdsdevices.sim import FastMotor

from .doc_stubs import insert_remove
from .epics_motor import IMS
from .inout import InOutRecordPositioner
from .interface import BaseInterface, FltMvInterface
from .pseudopos import (PseudoPositioner, PseudoSingleInterface,
                        pseudo_position_argument, real_position_argument)
from .utils import get_status_float, get_status_value

logger = logging.getLogger(__name__)


class H1N(InOutRecordPositioner):
    states_list = ['OUT', 'C', 'Si']
    in_states = ['C', 'Si']
    _states_alias = {'C': 'IN'}
    _transmission = {'C': 0.8, 'Si': 0.7}


class YagLom(InOutRecordPositioner):
    states_list = ['OUT', 'YAG', 'SLIT1', 'SLIT2', 'SLIT3']
    in_states = ['YAG', 'SLIT1', 'SLIT2', 'SLIT3']
    _states_alias = {'YAG': 'IN'}


class Dectris(InOutRecordPositioner):
    states_list = ['OUT', 'DECTRIS', 'SLIT1', 'SLIT2', 'SLIT3', 'OUTLOW']
    in_states = ['DECTRIS', 'SLIT1', 'SLIT2', 'SLIT3']
    out_states = ['OUT', 'OUTLOW']
    _states_alias = {'DECTRIS': 'IN'}


class Diode(InOutRecordPositioner):
    states_list = ['OUT', 'IN']


class Foil(InOutRecordPositioner):
    states_list = ['OUT']
    in_states = []

    def __init__(self, prefix, *args, **kwargs):
        if 'XPP' in prefix:
            self.in_states = ['Mo', 'Zr', 'Zn', 'Cu', 'Ni', 'Fe', 'Ti']
        elif 'XCS' in prefix:
            self.in_states = ['Mo', 'Zr', 'Ge', 'Cu', 'Ni', 'Fe', 'Ti']
        self.states_list = ['OUT'] + self.in_states
        super().__init__(prefix, *args, **kwargs)


class CHI1(InOutRecordPositioner):
    """Rotation axis, it does not have an `OUT` state."""
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class CHI2(InOutRecordPositioner):
    """Rotation axis, it does not have an `OUT` state."""
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class H2N(InOutRecordPositioner):
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class Y1(InOutRecordPositioner):
    """Vertical y motion. Does not have an `OUT` state."""
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class Y2(InOutRecordPositioner):
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class CrystalTower1(BaseInterface, Device):
    """
    LODCM Crystal Tower 1.

    Has the Si and C crystals with 2 angles and 5 linear motions.
    The `h1n_state` brings the crystal into the beam, moving horizontally
    (normal to the beam and parallel to the ground). It is also the only axis
    that can fully clear the crystal assembly from the beam. If h1n state is
    `OUT` and if we were to insert into the beam, we would be aligned to the C
    crystal.
    The `y1_state` brings the crystal into the beam, moving vertically
    (normal to the beam and normal to the ground).
    The `chi1_state` rotates the crystal assembly.

    Parameters
    ----------
    prefix : str
        Epics base Pv prefix.
    name : str, keyword-only
        The name of this device.
    """
    # x, y, and z are on the base but not touched in normal operations
    z1 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:04',
              kind='normal', doc='LOM Xtal1 Z')
    x1 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:05',
              kind='normal', doc='LOM Xtal1 X')
    y1 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:06',
              kind='normal', doc='LOM Xtal1 Y')
    # theta movement
    th1 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:07',
               kind='normal', doc='LOM Xtal1 Theta')
    # chi movement
    chi1 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:08',
                kind='normal', doc='LOM Xtal1 Chi')
    # normal to the crystal surface movement
    h1n = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:09',
               kind='normal', doc='LOM Xtal1 Hn')
    # paralell to the crystal surface movement
    h1p = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:20',
               kind='normal', doc='LOM Xtal1 Hp')

    # states
    h1n_state = Cpt(H1N, ':H1N', kind='hinted')
    y1_state = Cpt(Y1, ':Y1', kind='normal')
    chi1_state = Cpt(CHI1, ':CHI1', kind='normal')

    # reflection pvs (3 1 1 1)
    diamond_reflection = Cpt(EpicsSignalRO, ':T1C:REF', kind='normal',
                             doc='Tower 1 Diamond crystal reflection')
    silicon_reflection = Cpt(EpicsSignalRO, ':T1Si:REF', kind='normal',
                             doc='Tower 1 Silicon crystal reflection')

    # motor offsets
    # the folowing are declared in Energy classes
    # th1_si, th1_c, z1_si, z1_c
    x1C = FCpt(OffsetMotor, prefix='{self._prefix}:X1:OFF_C',
               motor_prefix='{self._hutch_prefix}:MON:MMS:05', kind='normal',
               add_prefix=('prefix', 'motor_prefix'),
               name='x1_c', doc='X1 motor offset for C [mm]')
    x1Si = FCpt(OffsetMotor, prefix='{self._prefix}:X1:OFF_Si',
                motor_prefix='{self._hutch_prefix}:MON:MMS:05', kind='normal',
                add_prefix=('prefix', 'motor_prefix'),
                name='x1_si', doc='X1 motor offset for Si [mm]')
    y1C = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:Y1:OFF_C',
               motor_prefix='{self._hutch_prefix}:MON:MMS:06', kind='normal',
               add_prefix=('prefix', 'motor_prefix'),
               name='y1_c', doc='Y1 motor offset for C [mm]')
    y1Si = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:Y1:OFF_Si',
                motor_prefix='{self._hutch_prefix}:MON:MMS:06', kind='normal',
                add_prefix=('prefix', 'motor_prefix'),
                name='y1_si', doc='Y1 motor offset for Si [mm]')
    chi1C = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:CHI1:OFF_C',
                 motor_prefix='{self._hutch_prefix}:MON:MMS:08', kind='normal',
                 add_prefix=('prefix', 'motor_prefix'),
                 name='chi1_c ', doc='Chi 1 motor offset for C [deg]')
    chi1Si = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:CHI1:OFF_Si',
                  motor_prefix='{self._hutch_prefix}:MON:MMS:08',
                  kind='normal', add_prefix=('prefix', 'motor_prefix'),
                  name='chi1_si', doc='Chi 1 motor offset for Si [deg]')
    h1nC = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:H1N:OFF_C',
                motor_prefix='{self._hutch_prefix}:MON:MMS:09', kind='normal',
                add_prefix=('prefix', 'motor_prefix'),
                name='', doc='H1n motor offset for C [mm]')
    h1nSi = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:H1N:OFF_Si',
                 motor_prefix='{self._hutch_prefix}:MON:MMS:09', kind='normal',
                 add_prefix=('prefix', 'motor_prefix'),
                 name='h1n_si', doc='H1n motor offset for Si [mm]')
    h1pC = FCpt(OffsetMotor, prefix='{self._prefix}:H1P:OFF_C',
                motor_prefix='{self._hutch_prefix}:MON:MMS:20', kind='normal',
                add_prefix=('prefix', 'motor_prefix'),
                name='h1p_c', doc='H1p motor offset for C [mm]')
    h1pSi = FCpt(OffsetMotor, prefix='{self._prefix}:H1P:OFF_Si',
                 motor_prefix='{self._hutch_prefix}:MON:MMS:20', kind='normal',
                 add_prefix=('prefix', 'motor_prefix'),
                 name='h1p_si', doc='H1p motor offset for Si [mm]')

    tab_component_names = True
    tab_whitelist = ['is_diamond', 'is_silicon', 'get_reflection',
                     'get_material']

    def __init__(self, prefix, *args, **kwargs):
        self._hutch_prefix = ''
        self._prefix = prefix
        if 'XPP' in prefix:
            self._hutch_prefix = 'XPP'
        elif 'XCS' in prefix:
            self._hutch_prefix = 'HFX'
        super().__init__(prefix, *args, **kwargs)

    def is_diamond(self):
        """Check if tower 1 is with Diamond (C) material."""
        return ((self.h1n_state.position == 'C' or
                 self.h1n_state.position == 'OUT') and
                self.y1_state.position == 'C' and
                self.chi1_state.position == 'C')

    def is_silicon(self):
        """Check if tower 1 is with Silicon (Si) material."""
        return ((self.h1n_state.position == 'Si' or
                 self.h1n_state.position == 'OUT') and
                self.y1_state.position == 'Si' and
                self.chi1_state.position == 'Si')

    def get_reflection(self):
        """
        Get crystal's reflection.

        Tries to get the reflection depending on the material in use.

        Returns
        -------
        reflection : tuple

        Raises
        ------
        ValueError
            When cannot determine the reflection.
        """
        reflection = None
        if self.is_diamond():
            reflection = self.diamond_reflection.get()
        elif self.is_silicon():
            reflection = self.silicon_reflection.get()

        if reflection is not None:
            return tuple(reflection)
        raise ValueError('Unable to determine the crystal reflection')

    def get_material(self):
        """
        Get the current material.

        Returns
        -------
        material : str
            Material of the crystal.

        Raises
        ------
        ValueError
            When the material could not be determined or is something else
             other than `Si` or `C`.
        """
        if self.is_diamond():
            return 'C'
        elif self.is_silicon():
            return 'Si'
        else:
            raise ValueError(
                "Unable to determine crystal material for Tower 1")

    def format_status_info(self, status_info):
        """Override status info handler to render the crystal tower 1."""
        t1_state = get_status_value(
            status_info, 'h1n_state', 'position')
        state = f'h1n_state: {t1_state}'
        hutch = ''
        if 'XPP' in self.prefix:
            hutch = 'XPP '
        elif 'XCS' in self.prefix:
            hutch = 'XCS '

        try:
            material = self.get_material()
        except Exception:
            material = 'Unknown'

        if material == 'C':
            configuration = 'Diamond'
        elif material == 'Si':
            configuration = 'Silicon'
        else:
            configuration = 'Unknown'

        try:
            ref = self.get_reflection()
            ref = ''.join(map(str, ref))
        except Exception:
            ref = 'Unknown'
        # tower 1
        z_units = get_status_value(
            status_info, 'z1', 'user_setpoint', 'units')
        z_user = get_status_float(
            status_info, 'z1', 'position')
        z_dial = get_status_float(
            status_info, 'z1', 'dial_position', 'value')

        x_units = get_status_value(
            status_info, 'x1', 'user_setpoint', 'units')
        x_user = get_status_float(status_info, 'tower1', 'x1', 'position')
        x_dial = get_status_float(
            status_info, 'x1', 'dial_position', 'value')

        th_units = get_status_value(
            status_info, 'th1', 'user_setpoint', 'units')
        th_user = get_status_float(
            status_info, 'th1', 'position')
        th_dial = get_status_float(
            status_info, 'th1', 'dial_position', 'value')

        chi_units = get_status_value(
            status_info, 'chi1', 'user_setpoint', 'units')
        chi_user = get_status_float(
            status_info, 'chi1', 'position')
        chi_dial = get_status_float(
            status_info, 'chi1', 'dial_position', 'value')

        y_units = get_status_value(
            status_info, 'y1', 'user_setpoint', 'units')
        y_user = get_status_float(
            status_info, 'y1', 'position')
        y_dial = get_status_float(
            status_info, 'y1', 'dial_position', 'value')

        hn_units = get_status_value(
            status_info, 'h1n', 'user_setpoint', 'units')
        hn_user = get_status_float(
            status_info, 'h1n', 'position')
        hn_dial = get_status_float(
            status_info, 'h1n', 'dial_position', 'value')

        hp_units = get_status_value(
            status_info, 'h1p', 'user_setpoint', 'units')
        hp_user = get_status_float(
            status_info, 'h1p', 'position')
        hp_dial = get_status_float(
            status_info, 'h1p', 'dial_position', 'value')

        return f"""\
{hutch}LODCM Crystal Tower 1
{state}
Current Configuration: {configuration} ({ref})
z [{z_units}]  {z_user} ({z_dial})
x [{x_units}]  {x_user} ({x_dial})
th [{th_units}]  {th_user} ({th_dial})
chi [{chi_units}]  {chi_user} ({chi_dial})
y [{y_units}]  {y_user} ({y_dial})
hn [{hn_units}]  {hn_user} ({hn_dial})
hp [{hp_units}]  {hp_user} ({hp_dial})
"""


class CrystalTower2(BaseInterface, Device):
    """
    LODCM Crystal Tower 2.

    Has the second Si and C crystals and a diode behind the crystals.

    Parameters
    ----------
    prefix : str
        Epics base Pv prefix.
    name : str
        The name of this device.
    """
    # x, y, and z are on the base but not touched in normal operations
    z2 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:10',
              kind='normal', doc='LOM Xtal2 Z')
    x2 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:11',
              kind='normal', doc='LOM Xtal2 X')
    y2 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:12',
              kind='normal', doc='LOM Xtal2 Y')
    # thata movement
    th2 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:13',
               kind='normal', doc='LOM Xtal2 Theta')
    # chi movement
    chi2 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:14',
                kind='normal', doc='LOM Xtal2 Chi')
    # normal to the crystal surface movement
    h2n = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:15',
               kind='normal', doc='LOM Xtal2 Hn')
    # in the DAQ for scanning in python, only used for commissioning
    diode2 = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:21',
                  kind='normal', doc='LOM Xtal2 PIPS')

    x2_retry_deadband = FCpt(EpicsSignalRO,
                             '{self._hutch_prefix}:MON:MMS:11.RDBD',
                             doc='Retry Deadband for x2', kind='omitted')
    z2_retry_deadband = FCpt(EpicsSignalRO,
                             '{self._hutch_prefix}:MON:MMS:10.RDBD',
                             doc='Retry Deadband for z2', kind='omitted')

    # states
    h2n_state = Cpt(H2N, ':H2N', kind='hinted')
    y2_state = Cpt(Y2, ':Y2', kind='normal')
    chi2_state = Cpt(CHI2, ':CHI2', kind='normal')

    # reflection pvs
    diamond_reflection = Cpt(EpicsSignalRO, ':T2C:REF', kind='normal',
                             doc='Tower 2 Diamond crystal reflection')
    silicon_reflection = Cpt(EpicsSignalRO, ':T2Si:REF', kind='normal',
                             doc='Tower 2 Silicon crystal reflection')

    # motor offsets
    # the following ones are declared in the Energy classes
    # th2_si, th2_c, z2_si, z2_c
    x2C = FCpt(OffsetMotor, prefix='{self._prefix}:X2:OFF_C', name='x2_c ',
               motor_prefix='{self._hutch_prefix}:MON:MMS:11',
               add_prefix=('prefix', 'motor_prefix'), kind='normal',
               doc='X2 motor offset for C [mm]')
    x2Si = FCpt(OffsetMotor, prefix='{self._prefix}:X2:OFF_Si', name='x2_si',
                motor_prefix='{self._hutch_prefix}:MON:MMS:11',
                add_prefix=('prefix', 'motor_prefix'), kind='normal',
                doc='X2 motor offset for Si [mm]')
    y2C = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:Y2:OFF_C',
               name='y2_c', motor_prefix='{self._hutch_prefix}:MON:MMS:12',
               add_prefix=('prefix', 'motor_prefix'), kind='normal',
               doc='Y2 motor offset for C [mm]')
    y2Si = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:Y2:OFF_Si',
                name='y2_si', motor_prefix='{self._hutch_prefix}:MON:MMS:12',
                add_prefix=('prefix', 'motor_prefix'), kind='normal',
                doc='Y2 motor offset for Si [mm]')
    chi2C = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:CHI2:OFF_C',
                 name='chi2_c', motor_prefix='{self._hutch_prefix}:MON:MMS:14',
                 add_prefix=('prefix', 'motor_prefix'), kind='normal',
                 doc='Chi 2 motor offset for C [deg]')
    chi2Si = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:CHI2:OFF_Si',
                  name='chi2_si',
                  motor_prefix='{self._hutch_prefix}:MON:MMS:14',
                  add_prefix=('prefix', 'motor_prefix'), kind='normal',
                  doc='Chi 2 motor offset for Si [deg]')
    h2nC = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:H2N:OFF_C',
                name='h2n_c', motor_prefix='{self._hutch_prefix}:MON:MMS:15',
                add_prefix=('prefix', 'motor_prefix'), kind='normal',
                doc=' H2n motor offset for C [mm]')
    h2nSi = FCpt(OffsetIMSWithPreset, prefix='{self._prefix}:H2N:OFF_Si',
                 name='h2n_si', motor_prefix='{self._hutch_prefix}:MON:MMS:15',
                 add_prefix=('prefix', 'motor_prefix'), kind='normal',
                 doc='H2n motor offset for Si [mm]')

    tab_component_names = True
    tab_whitelist = ['is_diamond', 'is_silicon', 'get_reflection',
                     'get_material']

    def __init__(self, prefix, *args, **kwargs):
        self._hutch_prefix = ''
        self._prefix = prefix
        if 'XPP' in prefix:
            self._hutch_prefix = 'XPP'
        elif 'XCS' in prefix:
            self._hutch_prefix = 'HFX'
        super().__init__(prefix, *args, **kwargs)

    def is_diamond(self):
        """Check if tower 2 is with Diamond (C) material."""
        return (self.h2n_state.position == 'C' and
                self.y2_state.position == 'C' and
                self.chi2_state.position == 'C')

    def is_silicon(self):
        """Check if tower 2 is with Silicon (Si) material."""
        return (self.h2n_state.position == 'Si' and
                self.y2_state.position == 'Si' and
                self.chi2_state.position == 'Si')

    def get_reflection(self):
        """
        Get crystal's reflection.

        Tries to get the reflection depending on the material in use.

        Returns
        -------
        reflection : tuple

        Raises
        ------
        ValueError
            When cannot determine the reflection.
        """
        reflection = None
        if self.is_diamond():
            reflection = self.diamond_reflection.get()
        elif self.is_silicon():
            reflection = self.silicon_reflection.get()

        if reflection is not None:
            return tuple(reflection)
        raise ValueError('Unable to determine the crystal reflection')

    def get_material(self):
        """
        Get the current material.

        Returns
        -------
        material : str
            Material of the crystal.

        Raises
        ------
        ValueError
            When the material could not be determined or is something else
             other than `Si` or `C`.
        """
        if self.is_diamond():
            return 'C'
        elif self.is_silicon():
            return 'Si'
        else:
            raise ValueError(
                "Unable to determine crystal material for Tower 2")

    def format_status_info(self, status_info):
        """Override status info handler to render the crystal tower 2."""
        t2_state = get_status_value(
            status_info, 'h2n_state', 'position')
        state = f'h2n_state: {t2_state}'
        hutch = ''
        if 'XPP' in self.prefix:
            hutch = 'XPP '
        elif 'XCS' in self.prefix:
            hutch = 'XCS '

        try:
            material = self.get_material()
        except Exception:
            material = 'Unknown'

        if material == 'C':
            configuration = 'Diamond'
        elif material == 'Si':
            configuration = 'Silicon'
        else:
            configuration = 'Unknown'

        try:
            ref = self.get_reflection()
            ref = ''.join(map(str, ref))
        except Exception:
            ref = 'Unknown'
        # tower 2
        z_units = get_status_value(
            status_info, 'z2', 'user_setpoint', 'units')
        z_user = get_status_float(
            status_info, 'z2', 'position')
        z_dial = get_status_float(
            status_info, 'z2', 'dial_position', 'value')

        x_units = get_status_value(
            status_info, 'x2', 'user_setpoint', 'units')
        x_user = get_status_float(
            status_info, 'x2', 'position')
        x_dial = get_status_float(
            status_info, 'x2', 'dial_position', 'value')

        th_units = get_status_value(
            status_info, 'th2', 'user_setpoint', 'units')
        th_user = get_status_float(
            status_info, 'th2', 'position')
        th_dial = get_status_float(
            status_info,  'th2', 'dial_position', 'value')

        chi_units = get_status_value(
            status_info, 'chi2', 'user_setpoint', 'units')
        chi_user = get_status_float(
            status_info,  'chi2', 'position')
        chi_dial = get_status_float(
            status_info,  'chi2', 'dial_position', 'value')

        y_units = get_status_value(
            status_info, 'y2', 'user_setpoint', 'units')
        y_user = get_status_float(
            status_info,  'y2', 'position')
        y_dial = get_status_float(
            status_info,  'y2', 'dial_position', 'value')

        hn_units = get_status_value(
            status_info, 'h2n', 'user_setpoint', 'units')
        hn_user = get_status_float(
            status_info,  'h2n', 'position')
        hn_dial = get_status_float(
            status_info,  'h2n', 'dial_position', 'value')

        diode_units = get_status_value(
            status_info, 'diode2', 'user_setpoint', 'units')
        diode_user = get_status_float(
            status_info, 'diode2', 'position')
        diode_dial = get_status_float(
            status_info, 'diode2', 'dial_position', 'value')

        return f"""\
{hutch}LODCM Crystal Tower 2
{state}
Current Configuration: {configuration} ({ref})
z [{z_units}]  {z_user} ({z_dial})
x [{x_units}]  {x_user} ({x_dial})
th [{th_units}]  {th_user} ({th_dial})
chi [{chi_units}]  {chi_user} ({chi_dial})
y [{y_units}]  {y_user} ({y_dial})
hn [{hn_units}]  {hn_user} ({hn_dial})
diode [{diode_units}]  {diode_user} ({diode_dial})
"""


class DiagnosticsTower(BaseInterface, Device):
    """
    LODCM Diagnostic Tower.

    Located midway between Crystal Tower 1 and Crystal Tower 2, in the center
    of rotation of the device.
    It contains a pips diode(dd), yag screen(dv), filters wheel (df)
    and vertical (dh) and horizontal slits (dd).

    Parameters
    ----------
    prefix : str
        Epics base PV prefix.
    name : str
        The name of this device.
    """
    # Located midway between T1 and T2 in the center of rotation of the device.
    # horizontal slits
    dh = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:16',
              kind='normal', doc='LOM Dia H')
    # vertical slits
    dv = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:17',
              kind='normal', doc='LOM Dia V')
    dr = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:19',
              kind='normal', doc='LOM Dia Theta')
    # filters wheel
    df = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:{self._df_suffix}',
              kind='normal', doc='LOM Dia Filter Wheel')
    # pips diode
    dd = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:18',
              kind='normal', doc='LOM Dia PIPS')
    # yag screen
    yag_zoom = FCpt(IMS, '{self._hutch_prefix}:MON:CLZ:01',
                    kind='normal', doc='LOM Zoom')

    tab_component_names = True

    def __init__(self, prefix, *args, **kwargs):
        # The df component has a different PV suffix in `XPP` vs `XCS`
        # XPP:MON:MMS:27 vs HFX:MON:MMS:22
        self._hutch_prefix = ''
        self._df_suffix = '27'
        if 'XPP' in prefix:
            self._hutch_prefix = 'XPP'
        elif 'XCS' in prefix:
            self._hutch_prefix = 'HFX'
            self._df_suffix = '22'

        super().__init__(prefix, *args, **kwargs)

    def format_status_info(self, status_info):
        """Override status info handler to render the diagnostics tower."""
        hutch = ''
        if 'XPP' in self.prefix:
            hutch = 'XPP '
        elif 'XCS' in self.prefix:
            hutch = 'XCS '
        # diagnostics
        dh_units = get_status_value(
            status_info, 'dh', 'user_setpoint', 'units')
        dh_user = get_status_float(
            status_info, 'dh', 'position')
        dh_dial = get_status_float(
            status_info, 'dh', 'dial_position', 'value')

        dv_units = get_status_value(
            status_info, 'dv', 'user_setpoint', 'units')
        dv_user = get_status_float(
            status_info,  'dv', 'position')
        dv_dial = get_status_float(
            status_info, 'dv', 'dial_position', 'value')

        dr_units = get_status_value(
            status_info, 'dr', 'user_setpoint', 'units')
        dr_user = get_status_float(
            status_info, 'dr', 'position')
        dr_dial = get_status_float(
            status_info, 'dr', 'dial_position', 'value')

        df_units = get_status_value(
            status_info, 'df', 'user_setpoint', 'units')
        df_user = get_status_float(
            status_info, 'df', 'position')
        df_dial = get_status_float(
            status_info, 'df', 'dial_position', 'value')

        dd_units = get_status_value(
            status_info, 'dd', 'user_setpoint', 'units')
        dd_user = get_status_float(
            status_info, 'dd', 'position')
        dd_dial = get_status_float(
            status_info, 'dd', 'dial_position', 'value')

        yag_zoom_units = get_status_value(status_info, 'yag_zoom',
                                          'user_setpoint', 'units')
        yag_zoom_user = get_status_float(status_info, 'yag_zoom', 'position',
                                         precision=0)
        yag_zoom_dial = get_status_float(status_info, 'yag_zoom',
                                         'dial_position', 'value', precision=0)
        return f"""\
{hutch}Diagnostics Tower
diag r [{dr_units}]  {dr_user} ({dr_dial})
diag h [{dh_units}]  {dh_user} ({dh_dial})
diag v [{dv_units}]  {dv_user} ({dv_dial})
filter [{df_units}]  {df_user} ({df_dial})
diode [{dd_units}]  {dd_user} ({dd_dial})
navitar zoom [{yag_zoom_units}]  {yag_zoom_user} ({yag_zoom_dial})
"""


class LODCMEnergySi(FltMvInterface, PseudoPositioner):
    """
    Energy calculations for the Si material.

    Assume material is 'Si' without checking if the crystal's materials are
    aligned for both towers.

    Parameters
    ----------
    prefix : str
        Epics base PV prefix.
    name : str
        The name of this device.
    """
    tower1 = FCpt(CrystalTower1, '{self._prefix}', kind='normal')
    tower2 = FCpt(CrystalTower2, '{self._prefix}', kind='normal')
    dr = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:19',
              kind='normal', doc='LOM Dia Theta')

    th1Si = FCpt(OffsetMotor, prefix='{self._prefix}:TH1:OFF_Si',
                 motor_prefix='{self._hutch_prefix}:MON:MMS:07',
                 add_prefix=('prefix', 'motor_prefix'), name='th1_si',
                 doc='Th1 motor offset for Si [deg]')
    th2Si = FCpt(OffsetMotor, prefix='{self._prefix}:TH2:OFF_Si',
                 motor_prefix='{self._hutch_prefix}:MON:MMS:13',
                 add_prefix=('prefix', 'motor_prefix'), name='th2_si',
                 doc='Th2 motor offset for Si [deg]')
    z1Si = FCpt(OffsetMotor, prefix='{self._prefix}:Z1:OFF_Si',
                name='z1_si',
                motor_prefix='{self._hutch_prefix}:MON:MMS:04',
                add_prefix=('prefix', 'motor_prefix'),
                doc='Z1 motor offset for Si [mm]')
    z2Si = FCpt(OffsetMotor, prefix='{self._prefix}:Z2:OFF_Si',
                name='z1_si',
                motor_prefix='{self._hutch_prefix}:MON:MMS:10',
                add_prefix=('prefix', 'motor_prefix'),
                doc='Z2 motor offset for Si [mm]')

    energy = Cpt(PseudoSingleInterface, egu='keV', kind='hinted')

    def __init__(self, prefix, *args, **kwargs):
        self._prefix = prefix
        self._hutch_prefix = ''
        if 'XPP' in self._prefix:
            self._hutch_prefix = 'XPP'
        elif 'XCS' in self._prefix:
            self._hutch_prefix = 'HFX'

        super().__init__(prefix=prefix, *args, **kwargs)

    def get_reflection(self):
        """
        Get the crystal reflection.

        Check both towers, and compare the if they match.
        If they do not match an error will be raised.

        Returns
        -------
        ref_1 : tuple
            Reflection of the two Crystal Towers.

        Raises
        ------
        ValueError
            When the reflection of first tower does not match the one of
            second tower.
        """
        ref_1 = self.tower1.get_reflection()
        ref_2 = self.tower2.get_reflection()
        if ref_1 != ref_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s',
                           ref_1, ref_2)
            raise ValueError('Invalid Crystal Arrangement')
        return ref_1

    def get_energy(self, material='Si', reflection=None):
        """
        Get photon energy from first tower in keV.

        Energy is determined by the first crystal (Theta motor).

        Parameters
        ----------
        material : str, optional
            Chemical formula. E.g.: `Si`
        reflection : tuple, optional
            Reflection of material. E.g.: `(1, 1, 1)`

        Returns
        -------
        energy : number
            Photon energy in keV.
        """
        reflection = reflection or self.get_reflection()
        th = self.th1Si.wm()
        length = (2 * np.sin(np.deg2rad(th)) *
                  diffraction.d_space(material, reflection))
        return common.wavelength_to_energy(length) / 1000

    def calc_geometry(self, energy, material='Si', reflection=None):
        """
        Calculate the lom geometry.

        Parameters
        ----------
        material : str, optional
            Chemical formula. E.g.: `Si`
        reflection : tuple, optional
            Reflection of material. E.g.: `(1, 1, 1)`

        Returns
        -------
        th, z : tuple
            Returns `theta` in degrees and `zm` TODO: what is this?
        """
        reflection = reflection or self.get_reflection()
        th, z = diffraction.get_lom_geometry(energy*1e3, material, reflection)
        return (th, z)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Calculate a RealPosition from a given PseudoPosition.

        If the pseudo positioner is here at `pseudo_pos`, then this is where
        my real motor should be.

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            The pseudo position input, a namedtuple.

        Returns
        -------
        real_pos : RealPosition
            The real position output, a namedtuple.
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)

        th, z = self.calc_geometry(energy=pseudo_pos.energy)

        return self.RealPosition(th1Si=th,
                                 th2Si=th,
                                 z1Si=-z,
                                 z2Si=z,
                                 dr=2*th)

    @real_position_argument
    def inverse(self, real_pos):
        """
        Calculate a PseudoPosition from a given RealPosition.

        If the real motor is at this `real_pos`, then this is where my pseudo
        position should be.

        Parameters
        ----------
        real_pos : RealPosition
            The real position input.

        Returns
        -------
        pseudo_pos : PseudoPosition
            The pseudo position output.
        """
        reflection = self.get_reflection()
        real_pos = self.RealPosition(*real_pos)
        length = (2 * np.sin(np.deg2rad(real_pos.th1Si))
                    * diffraction.d_space('Si', reflection))
        if length == 0:
            # don't bother transforming this
            # TODO maybe catch error in common.wave.. when send 0
            return 0
        energy = common.wavelength_to_energy(length) / 1000
        return self.PseudoPosition(energy=energy)

    def format_status_info(self, status_info):
        """Override status info handler to render the energy si."""
        hutch = ''
        if 'XPP' in self.prefix:
            hutch = 'XPP '
        elif 'XCS' in self.prefix:
            hutch = 'XCS '

        try:
            material = self.get_material()
        except Exception:
            material = 'Unknown'

        if material == 'C':
            configuration = 'Diamond'
        elif material == 'Si':
            configuration = 'Silicon'
        else:
            configuration = 'Unknown'

        try:
            energy = self.get_energy()
            energy = "{:.4f}".format(energy)
        except Exception:
            energy = 'Unknown'

        try:
            ref = self.get_reflection()
            ref = ''.join(map(str, ref))
        except Exception:
            ref = 'Unknown'

            return f"""\
{hutch}LODCM Energy Si
Current Configuration: {configuration} ({ref})
Photon Energy: {energy} [keV]
"""


class LODCMEnergyC(FltMvInterface, PseudoPositioner):
    """
    Energy calculations for the C material.

    Assume material is 'C' without checking if the crystal's materials are
    aligned for both towers.

    Parameters
    ----------
    prefix : str
        Epics base PV prefix.
    name : str
        The name of this device.
    """
    tower1 = FCpt(CrystalTower1, '{self._prefix}', kind='normal')
    tower2 = FCpt(CrystalTower2, '{self._prefix}', kind='normal')
    dr = FCpt(IMS, '{self._hutch_prefix}:MON:MMS:19',
              kind='normal', doc='LOM Dia Theta')

    th1C = FCpt(OffsetMotor, prefix='{self._prefix}:TH1:OFF_C',
                name='th1_c',
                motor_prefix='{self._hutch_prefix}:MON:MMS:07',
                add_prefix=('prefix', 'motor_prefix'),
                doc='Th1 motor offset for C [deg]')
    th2C = FCpt(OffsetMotor, prefix='{self._prefix}:TH2:OFF_C',
                name='th2_c',
                motor_prefix='{self._hutch_prefix}:MON:MMS:13',
                add_prefix=('prefix', 'motor_prefix'),
                doc='Th2 motor offset for C [deg]')
    z1C = FCpt(OffsetMotor, prefix='{self._prefix}:Z1:OFF_C', name='z1_c',
               motor_prefix='{self._hutch_prefix}:MON:MMS:04',
               add_prefix=('prefix', 'motor_prefix'),
               doc='Z1 motor offset for C [mm]')
    z2C = FCpt(OffsetMotor, prefix='{self._prefix}:Z2:OFF_C', name='z1_c',
               motor_prefix='{self._hutch_prefix}:MON:MMS:10',
               add_prefix=('prefix', 'motor_prefix'),
               doc='Z2 motor offset for C [mm]')

    energy = Cpt(PseudoSingleInterface, egu='keV', kind='hinted')

    def __init__(self, prefix, *args, **kwargs):
        self._prefix = prefix
        self._hutch_prefix = ''
        if 'XPP' in self._prefix:
            self._hutch_prefix = 'XPP'
        elif 'XCS' in self._prefix:
            self._hutch_prefix = 'HFX'

        super().__init__(prefix=prefix, *args, **kwargs)

    def get_reflection(self):
        """
        Get the crystal reflection.

        Check both towers, and compare the if they match.
        If they do not match an error will be raised.

        Returns
        -------
        ref_1 : tuple
            Reflection of the two Crystal Towers.

        Raises
        ------
        ValueError
            When the reflection of first tower does not match the one of
            second tower.
        """
        ref_1 = self.tower1.get_reflection()
        ref_2 = self.tower2.get_reflection()
        if ref_1 != ref_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s',
                           ref_1, ref_2)
            raise ValueError('Invalid Crystal Arrangement')
        return ref_1

    def get_energy(self, material='C', reflection=None):
        """
        Get photon energy from first tower in keV.

        Energy is determined by the first crystal (Theta motor).

        Parameters
        ----------
        material : str, optional
            Chemical formula. Defaults to `C`
        reflection : tuple, optional
            Reflection of material. E.g.: `(1, 1, 1)`

        Returns
        -------
        energy : number
            Photon energy in keV.
        """
        reflection = reflection or self.get_reflection()
        th = self.th1C.wm()
        length = (2 * np.sin(np.deg2rad(th)) *
                  diffraction.d_space(material, reflection))
        return common.wavelength_to_energy(length) / 1000

    def calc_geometry(self, energy, material='C', reflection=None):
        """
        Calculate the lom geometry.

        Parameters
        ----------
        material : str, optional
            Chemical formula. Defaults to `C`
        reflection : tuple, optional
            Reflection of material. E.g.: `(1, 1, 1)`

        Returns
        -------
        th, z : tuple
            Returns `theta` in degrees and `zm` TODO: what is this?
        """
        reflection = reflection or self.get_reflection()
        th, z = diffraction.get_lom_geometry(energy*1e3, material, reflection)
        return (th, z)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Calculate a RealPosition from a given PseudoPosition.

        If the pseudo positioner is here at `pseudo_pos`, then this is where
        my real motor should be.

        Parameters
        ----------
        pseudo_pos : PseudoPosition
            The pseudo position input, a namedtuple.

        Returns
        -------
        real_pos : RealPosition
            The real position output, a namedtuple.
        """
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        th, z = self.calc_geometry(energy=pseudo_pos.energy)

        return self.RealPosition(th1C=th,
                                 th2C=th,
                                 z1C=-z,
                                 z2C=z,
                                 dr=2*th)

    @real_position_argument
    def inverse(self, real_pos):
        """
        Calculate a PseudoPosition from a given RealPosition.

        If the real motor is at this `real_pos`, then this is where my pseudo
        position should be.

        Parameters
        ----------
        real_pos : RealPosition
            The real position input.

        Returns
        -------
        pseudo_pos : PseudoPosition
            The pseudo position output.
        """
        reflection = self.get_reflection()
        real_pos = self.RealPosition(*real_pos)
        length = (2 * np.sin(np.deg2rad(real_pos.th1C))
                    * diffraction.d_space('C', reflection))
        if length == 0:
            # don't bother transforming this
            # TODO maybe catch error in common.wave.. when send 0
            return 0
        energy = common.wavelength_to_energy(length) / 1000
        return self.PseudoPosition(energy=energy)

    def format_status_info(self, status_info):
        """Override status info handler to render the energy c."""
        hutch = ''
        if 'XPP' in self.prefix:
            hutch = 'XPP '
        elif 'XCS' in self.prefix:
            hutch = 'XCS '

        try:
            material = self.get_material()
        except Exception:
            material = 'Unknown'

        if material == 'C':
            configuration = 'Diamond'
        elif material == 'Si':
            configuration = 'Silicon'
        else:
            configuration = 'Unknown'

        try:
            energy = self.get_energy()
            energy = "{:.4f}".format(energy)
        except Exception:
            energy = 'Unknown'

        try:
            ref = self.get_reflection()
            ref = ''.join(map(str, ref))
        except Exception:
            ref = 'Unknown'

            return f"""\
{hutch}LODCM Energy C
Current Configuration: {configuration} ({ref})
Photon Energy: {energy} [keV]
"""


class LODCM(BaseInterface, Device):
    """
    Large Offset Dual Crystal Monochromator.

    This is the device that allows XPP and XCS to multiplex with downstream
    hutches. It contains two crystals that steer/split the beam and a number of
    diagnostic devices between them. Beam can continue onto the main line, onto
    the mono line, onto both, or onto neither.

    Tower 1 has the Si and C crystals with 2 angles and 5 linear motions.
    Tower 2 has the second Si and C crystals and a diode behind the crystals.

    Parameters
    ----------
    prefix : str
        The PV prefix.

    name : str
        The name of this device.

    main_line : str, optional
        Name of the main, no-bounce beamline.

    mono_line : str, optional
        Name of the mono, double-bounce beamline.
    """
    yag = Cpt(YagLom, ":DV", kind='omitted')
    dectris = Cpt(Dectris, ":DH", kind='omitted')
    diode = Cpt(Diode, ":DIODE", kind='omitted')
    foil = Cpt(Foil, ":FOIL", kind='omitted')

    tower1 = FCpt(CrystalTower1, '{self._prefix}', name='T1',
                  kind='normal')
    tower2 = FCpt(CrystalTower2, '{self._prefix}', name='T2',
                  kind='normal')
    # diagnostics tower
    diag_tower = FCpt(DiagnosticsTower, '{self._prefix}', name='DT',
                      kind='normal')

    energy_si = FCpt(LODCMEnergySi, '{self._prefix}', kind='normal')
    energy_c = FCpt(LODCMEnergyC, '{self._prefix}', kind='normal')
    # QIcon for UX
    _icon = 'fa.share-alt-square'

    tab_whitelist = ['h1n_state', 'yag', 'dectris', 'diode', 'foil',
                     'remove_dia', 'tower1', 'tower2',
                     'diag_tower', 'calc']

    def __init__(self, prefix, *, name, main_line='MAIN', mono_line='MONO',
                 **kwargs):
        self._prefix = prefix
        self._hutch_prefix = ''
        if 'XPP' in self._prefix:
            self._hutch_prefix = 'XPP'
        elif 'XCS' in self._prefix:
            self._hutch_prefix = 'HFX'

        super().__init__(prefix, name=name, **kwargs)
        self.main_line = main_line
        self.mono_line = mono_line
        # first tower
        self.z1 = self.tower1.z1
        self.x1 = self.tower1.x1
        self.y1 = self.tower1.y1
        self.th1 = self.tower1.th1
        self.chi1 = self.tower1.chi1
        self.h1n = self.tower1.h1n
        self.h1p = self.tower1.h1p
        # second tower
        self.z2 = self.tower2.z2
        self.x2 = self.tower2.x2
        self.y2 = self.tower2.y2
        self.th2 = self.tower2.th2
        self.chi2 = self.tower2.chi2
        self.h2n = self.tower2.h2n
        self.diode2 = self.tower2.diode2
        # diagnostic tower
        self.dh = self.diag_tower.dh
        self.dv = self.diag_tower.dv
        self.dr = self.diag_tower.dr
        self.df = self.diag_tower.df
        self.dd = self.diag_tower.dd
        self.yag_zoom = self.diag_tower.yag_zoom
        # states
        self.h1n_state = self.tower1.h1n_state
        self.y1_state = self.tower1.y1_state
        self.chi1_state = self.tower1.chi1_state
        self.h2n_state = self.tower2.h2n_state
        self.y2_state = self.tower2.y2_state
        self.chi2_state = self.tower2.chi2_state
        # # offset positioners - tower 1
        self.th1Si = self.energy_si.th1Si
        self.z1Si = self.energy_si.z1Si
        self.th1C = self.energy_c.th1C
        self.z1C = self.energy_c.z1C

        self.x1C = self.tower1.x1C
        self.x1Si = self.tower1.x1Si
        self.y1C = self.tower1.y1C
        self.y1Si = self.tower1.y1Si
        self.chi1C = self.tower1.chi1C
        self.chi1Si = self.tower1.chi1Si
        self.h1nC = self.tower1.h1nC
        self.h1nSi = self.tower1.h1nSi
        self.h1pC = self.tower1.h1pC
        self.h1pSi = self.tower1.h1pSi
        # # offset positioners - tower 2
        self.th2Si = self.energy_si.th2Si
        self.z2Si = self.energy_si.z2Si
        self.th2C = self.energy_c.th2C
        self.z2C = self.energy_c.z2C

        self.x2C = self.tower2.x2C
        self.x2Si = self.tower2.x2Si
        self.y2C = self.tower2.y2C
        self.y2Si = self.tower2.y2Si
        self.chi2C = self.tower2.chi2C
        self.chi2Si = self.tower2.chi2Si
        self.h2nC = self.tower2.h2nC
        self.h2nSi = self.tower2.h2nSi

    @property
    def energy(self):
        material = self.get_material()
        if material == 'C':
            return self.energy_c
        elif material == 'Si':
            return self.energy_si
        # return energy_c as default if could not determine the material
        # TODO consider "energy" proxy motor object that picks where to
        # forward the commands instead of this property
        return self.energy_c

    @property
    def inserted(self):
        """Returns `True` if either h1n crystal is in."""
        return self.h1n_state.inserted

    @property
    def removed(self):
        """Returns `True` if neither h1n crystal is in."""
        return self.h1n_state.removed

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """Moves the h1n crystal out of the beam."""
        return self.h1n_state.remove(moved_cb=moved_cb, timeout=timeout,
                                     wait=wait)

    @property
    def transmission(self):
        """Returns h1n's transmission value."""
        return self.h1n_state.transmission

    @property
    def branches(self):
        """Returns possible destinations as a list of strings."""
        return [self.main_line, self.mono_line]

    @property
    def destination(self):
        """
        Which beamline the light is reaching.

        Indeterminate states will show as blocked.

        Returns
        -------
        destination : list of str
            `.main_line` if the light continues on the main line.
            `.mono_line` if the light continues on the mono line.
        """

        if self.h1n_state.position == 'OUT':
            dest = [self.main_line]
        elif self.h1n_state.position == 'Si':
            dest = [self.mono_line]
        elif self.h1n_state.position == 'C':
            dest = [self.main_line, self.mono_line]
        else:
            dest = []

        if not self._dia_clear and self.mono_line in dest:
            dest.remove(self.mono_line)

        return dest

    @property
    def _dia_clear(self):
        """
        Check if the diagnostics are clear. All but the diode may prevent beam.

        Returns
        -------
        diag_clear : bool
            :keyword:`False` if the diagnostics will prevent beam.
        """

        yag_clear = self.yag.removed
        dectris_clear = self.dectris.removed
        foil_clear = self.foil.removed
        return all((yag_clear, dectris_clear, foil_clear))

    def remove_dia(self, moved_cb=None, timeout=None, wait=False):
        """Remove all diagnostic components."""
        logger.debug('Removing %s diagnostics', self.name)
        status = NullStatus()
        for dia in (self.yag, self.dectris, self.diode, self.foil):
            status = status & dia.remove(timeout=timeout, wait=False)

        if moved_cb is not None:
            status.add_callback(functools.partial(moved_cb, obj=self))

        if wait:
            status_wait(status)

        return status

    remove_dia.__doc__ += insert_remove

    def get_reflection(self):
        """
        Get the crystal reflection.

        Check both towers, and compare the if they match.
        If they do not match an error will be raised.

        Returns
        -------
        ref_1 : tuple
            Reflection of the two Crystal Towers.

        Raises
        ------
        ValueError
            When the reflection of first tower does not match the one of
            second tower.
        """
        ref_1 = self.tower1.get_reflection()
        ref_2 = self.tower2.get_reflection()
        if ref_1 != ref_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s',
                           ref_1, ref_2)
            raise ValueError('Invalid Crystal Arrangement')
        return ref_1

    def get_material(self):
        """
        Get the current crystals material.

        Parameters
        ----------
        check : bool
            Indicates if an exception should occure in case it could not
            determine the material for a tower.

        Returns
        -------
        m_1 : str
            Crystals material.
        """
        m_1 = self.tower1.get_material()
        m_2 = self.tower2.get_material()
        if m_1 != m_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s', m_1, m_2)
            raise ValueError('Invalid Crystal Arrangement.')
        return m_1

    def get_energy(self, material=None, reflection=None):
        """
        Get photon energy from first tower in keV.

        Energy is determined by the first crystal (Theta motor).

        Parameters
        ----------
        material : str, optional
            Chemical formula.
        reflection : tuple, optional
            Reflection of material. E.g.: `(1, 1, 1)`

        Returns
        -------
        energy : number
            Photon energy in keV.
        """
        material = material or self.get_material()
        reflection = reflection or self.get_reflection()
        if material == 'Si':
            return self.energy_si.get_energy()
        elif material == 'C':
            return self.energy_c.get_energy()
        else:
            raise ValueError('Cannot decide the energy motor because could not'
                             ' determine the material.')

    def calc_geometry(self, energy, material=None, reflection=None):
        """
        Calculate the lom geometry.

        Parameters
        ----------
        material : str, optional
            Chemical formula. E.g.: `Si`
        reflection : tuple, optional
            Reflection of material. E.g.: `(1, 1, 1)`

        Returns
        -------
        th, z : tuple
        """
        # try to determine the material and reflection:
        material = material or self.get_material()
        reflection = reflection or self.get_reflection()
        return self.energy.calc_geometry(energy, material, reflection)

    def set_energy(self, energy, material=None, reflection=None):
        """
        Set the current positions of th1, th2, z1 and z2 offset motors.

        Parameters
        ----------
        energy : number
            Energy in keV.
        material : str, optional
            Crystal material. E.g.: `Si`
        reflection : tuple, optional
            Crystal's reflections. E.g.: `(1,1,1)`
        """
        # try to determine the material and reflection:
        material = material or self.get_material()
        reflection = reflection or self.get_reflection()
        th, z = diffraction.get_lom_geometry(energy * 1e3, material,
                                             reflection)
        if material == 'Si':
            self.th1Si.set_current_position(th)
            self.th2Si.set_current_position(th)
            self.z1Si.set_current_position(-z)
            self.z2Si.set_current_position(z)
        elif material == 'C':
            self.th1C.set_current_position(th)
            self.th2C.set_current_position(th)
            self.z1C.set_current_position(-z)
            self.z2C.set_current_position(z)
        else:
            raise ValueError("Invalid material: %s", material)

    def tweak_x(self, x_value, material=None, wait=False):
        """
        Tweak some motors to center the beam on YAG2 horizontally based on
        the calibrated s4 position.

        Parameters
        ----------
        x_value : number
            The value that we want to move `x2` by from current position.
        material : str, optional
            Crystal material. E.g.: `Si`
        wait : bool, optional
            Wait for motion to complete if wait is `True`. Defaults to `False`.
        """
        # try to determine the material:
        material = material or self.get_material()
        if material == 'Si':
            th = self.th2Si.wm()
        elif material == 'C':
            th = self.th2C.wm()
        else:
            raise ValueError("Invalid material: %s", material)
        z_value = x_value / common.tand(2 * th)
        start_x = self.x2.wm()
        start_z = self.z2.wm()
        self.x2.mvr(x_value, wait=wait)
        self.z2.mvr(z_value, wait=wait)
        end_x = self.x2.wm()
        end_z = self.z2.wm()
        dx = end_x - start_x
        dz = end_z - start_z

        if abs(dx - x_value) > self.tower2.x2_retry_deadband.get():
            logger.warning("x2 did not reach to the desired position of %f! "
                           "Check the motors, now at: %f, deadband %f" % (
                               start_x + x_value, end_x, self.x2.position))
        if abs(dz - z_value) > self.tower2.z2_retry_deadband.get():
            logger.warning("z2 did not reach the desired position of %f! "
                           "Check the motors, now at %f, deadband %f" % (
                               start_z + z_value, end_z, self.z2.position))

    def tweak_parallel(self, p_value, material=None, wait=False):
        """
        Tweak the `x2` and `z2` motors.

        Parameters
        ----------
        p_value : number
            The number we want to use to tweak the position of x2 and z2
        material : str, optional
            Crystal material. E.g.: `Si`
        wait : bool
            Wait for motion to complete if wait is `True`. Defaults to `False`.
        """
        # try to determine the material:
        material = material or self.get_material()
        if material == 'Si':
            th = self.th2Si.wm()
            self.x2.mvr(p_value * np.sin(th * np.pi / 180), wait=wait)
            self.z2.mvr(p_value * np.cos(th * np.pi / 180), wait=wait)
        elif material == 'C':
            th = self.th2C.wm()
            self.x2.mvr(p_value * np.sin(th * np.pi / 180), wait=wait)
            self.z2.mvr(p_value * np.cos(th * np.pi / 180), wait=wait)
        else:
            raise ValueError("Invalid material: %s", material)

    def wait_energy(self, timeout=None):
        """
        Block all these motors untill some action completes.

        Parameters
        ----------
        timeout: number, optional
            If None, wait indefinitely until the status finishes.
            Defaults to None.
        """
        self.th1.wait(timeout=timeout)
        self.th2.wait(timeout=timeout)
        self.dr.wait(timeout=timeout)
        self.z1.wait(timeout=timeout)
        self.z2.wait(timeout=timeout)

    def format_status_info(self, status_info):
        """Override status info handler to render the lodcm."""
        t1_state = get_status_value(
            status_info, 'tower1', 'h1n_state', 'position')
        t2_state = get_status_value(
            status_info, 'tower2', 'h2n_state', 'position')
        state = ''
        hutch = ''
        if 'XPP' in self.prefix:
            hutch = 'XPP '
            state = f'Crystal 1 state: {t1_state}'
        elif 'XCS' in self.prefix:
            hutch = 'XCS '
            state = f'Crystal 1 state: {t1_state}'
            state = f'{state}\nCrystal 2 state: {t2_state}'

        try:
            material = self.get_material()
        except Exception:
            material = 'Unknown'

        if material == 'C':
            configuration = 'Diamond'
        elif material == 'Si':
            configuration = 'Silicon'
        else:
            configuration = 'Unknown'

        try:
            energy = self.get_energy()
            energy = "{:.4f}".format(energy)
        except Exception:
            energy = 'Unknown'

        try:
            ref = self.get_reflection()
            ref = ''.join(map(str, ref))
        except Exception:
            ref = 'Unknown'
        # tower 1
        z_units = get_status_value(
            status_info, 'tower1', 'z1', 'user_setpoint', 'units')
        z_user = get_status_float(
            status_info, 'tower1', 'z1', 'position')
        z_dial = get_status_float(
            status_info, 'tower1', 'z1', 'dial_position', 'value')

        x_units = get_status_value(
            status_info, 'tower1', 'x1', 'user_setpoint', 'units')
        x_user = get_status_float(status_info, 'tower1', 'x1', 'position')
        x_dial = get_status_float(
            status_info, 'tower1', 'x1', 'dial_position', 'value')

        th_units = get_status_value(
            status_info, 'tower1', 'th1', 'user_setpoint', 'units')
        th_user = get_status_float(
            status_info, 'tower1', 'th1', 'position')
        th_dial = get_status_float(
            status_info, 'tower1', 'th1', 'dial_position', 'value')

        chi_units = get_status_value(
            status_info, 'tower1', 'chi1', 'user_setpoint', 'units')
        chi_user = get_status_float(
            status_info, 'tower1', 'chi1', 'position')
        chi_dial = get_status_float(
            status_info, 'tower1', 'chi1', 'dial_position', 'value')

        y_units = get_status_value(
            status_info, 'tower1', 'y1', 'user_setpoint', 'units')
        y_user = get_status_float(
            status_info, 'tower1', 'y1', 'position')
        y_dial = get_status_float(
            status_info, 'tower1', 'y1', 'dial_position', 'value')

        hn_units = get_status_value(
            status_info, 'tower1', 'h1n', 'user_setpoint', 'units')
        hn_user = get_status_float(
            status_info, 'tower1', 'h1n', 'position')
        hn_dial = get_status_float(
            status_info, 'tower1', 'h1n', 'dial_position', 'value')

        hp_units = get_status_value(
            status_info, 'tower1', 'h1p', 'user_setpoint', 'units')
        hp_user = get_status_float(
            status_info, 'tower1', 'h1p', 'position')
        hp_dial = get_status_float(
            status_info, 'tower1', 'h1p', 'dial_position', 'value')

        diode_units = get_status_value(
            status_info, 'tower1', 'diode2', 'user_setpoint', 'units')
        diode_user = get_status_float(
            status_info, 'tower1', 'diode', 'position')
        diode_dial = get_status_float(
            status_info, 'tower1', 'diode', 'dial_position', 'value')
        # tower 2
        z2_user = get_status_float(
            status_info, 'tower2', 'z2', 'position')
        z2_dial = get_status_float(
            status_info, 'tower2', 'z2', 'dial_position', 'value')

        x2_user = get_status_float(
            status_info, 'tower2', 'x2', 'position')
        x2_dial = get_status_float(
            status_info, 'tower2', 'x2', 'dial_position', 'value')

        th2_user = get_status_float(
            status_info, 'tower2', 'th2', 'position')
        th2_dial = get_status_float(
            status_info, 'tower2', 'th2', 'dial_position', 'value')

        chi2_user = get_status_float(
            status_info, 'tower2', 'chi2', 'position')
        chi2_dial = get_status_float(
            status_info, 'tower2', 'chi2', 'dial_position', 'value')

        y2_user = get_status_float(
            status_info, 'tower2', 'y2', 'position')
        y2_dial = get_status_float(
            status_info, 'tower2', 'y2', 'dial_position', 'value')

        hn2_user = get_status_float(
            status_info, 'tower2', 'h2n', 'position')
        hn2_dial = get_status_float(
            status_info, 'tower2', 'h2n', 'dial_position', 'value')

        hp2_user = get_status_float(
            status_info, 'tower2', 'h2p', 'position')
        hp2_dial = get_status_float(
            status_info, 'tower2', 'h2p', 'dial_position', 'value')

        diode2_user = get_status_float(
            status_info, 'tower2', 'diode2', 'position')
        diode2_dial = get_status_float(
            status_info, 'tower2', 'diode2', 'dial_position', 'value')
        # diagnostics
        dh_units = get_status_value(
            status_info, 'diag_tower', 'dh', 'user_setpoint', 'units')
        dh_user = get_status_float(
            status_info, 'diag_tower', 'dh', 'position')
        dh_dial = get_status_float(
            status_info, 'diag_tower', 'dh', 'dial_position', 'value')

        dv_units = get_status_value(
            status_info, 'diag_tower', 'dv', 'user_setpoint', 'units')
        dv_user = get_status_float(
            status_info, 'diag_tower', 'dv', 'position')
        dv_dial = get_status_float(
            status_info, 'diag_tower', 'dv', 'dial_position', 'value')

        dr_units = get_status_value(
            status_info, 'diag_tower', 'dr', 'user_setpoint', 'units')
        dr_user = get_status_float(
            status_info, 'diag_tower', 'dr', 'position')
        dr_dial = get_status_float(
            status_info, 'diag_tower', 'dr', 'dial_position', 'value')

        df_units = get_status_value(
            status_info, 'diag_tower', 'df', 'user_setpoint', 'units')
        df_user = get_status_float(
            status_info, 'diag_tower', 'df', 'position')
        df_dial = get_status_float(
            status_info, 'diag_tower', 'df', 'dial_position', 'value')

        dd_units = get_status_value(
            status_info, 'diag_tower', 'dd', 'user_setpoint', 'units')
        dd_user = get_status_float(
            status_info, 'diag_tower', 'dd', 'position')
        dd_dial = get_status_float(
            status_info, 'diag_tower', 'dd', 'dial_position', 'value')

        yag_zoom_units = get_status_value(status_info, 'diag_tower',
                                          'yag_zoom', 'user_setpoint', 'units')
        yag_zoom_user = get_status_float(status_info, 'diag_tower',
                                         'yag_zoom', 'position', precision=0)
        yag_zoom_dial = get_status_float(status_info, 'diag_tower',
                                         'yag_zoom', 'dial_position', 'value',
                                         precision=0)

        def form(left_str, center_str, right_str):
            return f'{left_str:<16}{center_str:>26}{right_str:>26}'

        return f"""\
{hutch}LODCM Motor Status Positions
{state}
Current Configuration: {configuration} ({ref})
Photon Energy: {energy} [keV]
-----------------------------------------------------------------
{form(' ', 'Crystal Tower 1', 'Crystal Tower 2')}
{form(f'z [{z_units}]', f'{z_user} ({z_dial})',
      f'{z2_user} ({z2_dial})')}
{form(f'x [{x_units}]', f'{x_user} ({x_dial})',
      f'{x2_user} ({x2_dial})')}
{form(f'th [{th_units}]', f'{th_user} ({th_dial})',
      f'{th2_user} ({th2_dial})')}
{form(f'chi [{chi_units}]', f'{chi_user} ({chi_dial})',
      f'{chi2_user} ({chi2_dial})')}
{form(f'y [{y_units}]', f'{y_user} ({y_dial})',
      f'{y2_user} ({y2_dial})')}
{form(f'hn [{hn_units}]', f'{hn_user} ({hn_dial})',
      f'{hn2_user} ({hn2_dial})')}
{form(f'hp [{hp_units}]', f'{hp_user} ({hp_dial})',
      f'{hp2_user} ({hp2_dial})')}
{form(f'diode [{diode_units}]', f'{diode_user} ({diode_dial})',
      f'{diode2_user} ({diode2_dial})')}
-----------------------------------------------------------------
{form(' ', 'Diagnostic Tower', ' ')}
{form(f'diag r [{dr_units}]', f'{dr_user} ({dr_dial})', '')}
{form(f'diag h [{dh_units}]', f'{dh_user} ({dh_dial})', '')}
{form(f'diag v [{dv_units}]', f'{dv_user} ({dv_dial})', '')}
{form(f'filter [{df_units}]', f'{df_user} ({df_dial})', '')}
{form(f'diode [{dd_units}]', f'{dd_user} ({dd_dial})', '')}
{form(f'navitar zoom [{yag_zoom_units}]',
      f'{yag_zoom_user} ({yag_zoom_dial})', '')}
"""


class SimFirstTower(CrystalTower1):
    """Crystal Tower 1 Simulator for Testing."""
    # first tower
    z1 = Cpt(FastMotor, limits=(-1000, 1000))
    x1 = Cpt(FastMotor, limits=(-1000, 1000))
    y1 = Cpt(FastMotor, limits=(-1000, 1000))
    th1 = Cpt(FastMotor, limits=(-1000, 1000))
    chi1 = Cpt(FastMotor, limits=(-1000, 1000))
    h1n = Cpt(FastMotor, limits=(-1000, 1000))
    h1p = Cpt(FastMotor, limits=(-1000, 1000))


class SimSecondTower(CrystalTower2):
    """Crystal Tower 2 Simulator for Testing."""
    # second tower
    z2 = Cpt(FastMotor, limits=(-1000, 1000))
    x2 = Cpt(FastMotor, limits=(-1000, 1000))
    y2 = Cpt(FastMotor, limits=(-1000, 1000))
    th2 = Cpt(FastMotor, limits=(-1000, 1000))
    chi2 = Cpt(FastMotor, limits=(-1000, 1000))
    h2n = Cpt(FastMotor, limits=(-1000, 1000))
    diode2 = Cpt(FastMotor, limits=(-1000, 1000))


class SimDiagnosticsTower(DiagnosticsTower):
    """Diagnostics Tower Simulator for Testing."""
    # diagnostic tower
    dh = Cpt(FastMotor, limits=(-1000, 1000))
    dv = Cpt(FastMotor, limits=(-1000, 1000))
    dr = Cpt(FastMotor, limits=(-1000, 1000))
    df = Cpt(FastMotor, limits=(-1000, 1000))
    dd = Cpt(FastMotor, limits=(-1000, 1000))
    yag_zoom = Cpt(FastMotor, limits=(-1000, 1000))


class SimEnergyC(LODCMEnergyC):
    """Energy C Simulator for Testing"""
    th1C = Cpt(FastMotor, limits=(-1000, 1000))
    th2C = Cpt(FastMotor, limits=(-1000, 1000))
    z1C = Cpt(FastMotor, limits=(-1000, 1000))
    z2C = Cpt(FastMotor, limits=(-1000, 1000))
    dr = Cpt(FastMotor, limits=(-1000, 1000))

    def get_reflection(self):
        return (1, 1, 1)


class SimEnergySi(LODCMEnergySi):
    """Energy Si Simulator for Testing"""
    th1Si = Cpt(FastMotor, limits=(-1000, 1000))
    th2Si = Cpt(FastMotor, limits=(-1000, 1000))
    z1Si = Cpt(FastMotor, limits=(-1000, 1000))
    z2Si = Cpt(FastMotor, limits=(-1000, 1000))
    dr = Cpt(FastMotor, limits=(-1000, 1000))

    def get_reflection(self):
        return (1, 1, 1)


class SimLODCM(LODCM):
    """LODCM Simulator for Testing"""
    tower1 = Cpt(SimFirstTower, 'TOWER:1', name='tower1')
    tower2 = Cpt(SimSecondTower, 'TOWER:2', name='tower2')
    diag_tower = Cpt(SimDiagnosticsTower, 'DIAG', name='diag')
    energy_si = Cpt(SimEnergySi, 'ENERGY:SI', name='energy_si')
    energy_c = Cpt(SimEnergyC, 'ENERGY:C', name='energy_c')

    def __init__(self, prefix, *args, **kwargs):

        super().__init__(prefix=prefix, *args, **kwargs)
        # first tower
        self.z1 = FastMotor(limits=(-1000, 1000))
        self.x1 = FastMotor(limits=(-1000, 1000))
        self.y1 = FastMotor(limits=(-1000, 1000))
        self.th1 = FastMotor(limits=(-1000, 1000))
        self.chi1 = FastMotor(limits=(-1000, 1000))
        self.h1n = FastMotor(limits=(-1000, 1000))
        self.h1p = FastMotor(limits=(-1000, 1000))
        # second tower
        self.z2 = FastMotor(limits=(-1000, 1000))
        self.x2 = FastMotor(limits=(-1000, 1000))
        self.y2 = FastMotor(limits=(-1000, 1000))
        self.th2 = FastMotor(limits=(-1000, 1000))
        self.chi2 = FastMotor(limits=(-1000, 1000))
        self.h2n = FastMotor(limits=(-1000, 1000))
        self.diode2 = FastMotor(limits=(-1000, 1000))
        # diagnostic tower
        self.dh = FastMotor(limits=(-1000, 1000))
        self.dv = FastMotor(limits=(-1000, 1000))
        self.dr = FastMotor(limits=(-1000, 1000))
        self.df = FastMotor(limits=(-1000, 1000))
        self.dd = FastMotor(limits=(-1000, 1000))
        self.yag_zoom = FastMotor(limits=(-1000, 1000))
