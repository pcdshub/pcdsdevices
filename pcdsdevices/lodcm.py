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

from ophyd.device import Component as Cpt, Device
from ophyd.sim import NullStatus
from ophyd.signal import EpicsSignalRO
from ophyd.status import wait as status_wait
import numpy as np
from pcdscalc import diffraction, common

from .component import UnrelatedComponent as UCpt
from ophyd.device import FormattedComponent as FCpt
from .doc_stubs import insert_remove
from .inout import InOutRecordPositioner
from .interface import BaseInterface, FltMvInterface
from .epics_motor import IMS
from .utils import get_status_value, get_status_float
from .pseudopos import (PseudoSingleInterface, PseudoPositioner,
                        pseudo_position_argument, real_position_argument)

logger = logging.getLogger(__name__)

LODCM_MOTORS = {
    # CRYSTAL TOWER ONE
    'z1': {'prefix': 'XPP:MON:MMS:04', 'description': 'LOM Xtal1 Z'},
    'x1': {'prefix': 'XPP:MON:MMS:05', 'description': 'LOM Xtal1 X'},
    'y1': {'prefix': 'XPP:MON:MMS:06', 'description': 'LOM Xtal1 Y'},
    'th1': {'prefix': 'XPP:MON:MMS:07', 'description': 'LOM Xtal1 Theta'},
    'ch1': {'prefix': 'XPP:MON:MMS:08', 'description': 'LOM Xtal1 Chi'},
    'h1n_m': {'prefix': 'XPP:MON:MMS:09', 'description': 'LOM Xtal1 Hn'},
    'h1p': {'prefix': 'XPP:MON:MMS:20', 'description': 'LOM Xtal1 Hp'},
    'th1f': {'prefix': 'XPP:MON:PIC:01', 'description': ''},
    'ch1f': {'prefix': 'XPP:MON:PIC:02', 'description': ''},
    # CRYSTAL TOWER TWO
    'z2': {'prefix': 'XPP:MON:MMS:10', 'description': 'LOM Xtal2 Z'},
    'x2': {'prefix': 'XPP:MON:MMS:11', 'description': 'LOM Xtal2 X'},
    'y2': {'prefix': 'XPP:MON:MMS:12', 'description': 'LOM Xtal2 Y'},
    'th2': {'prefix': 'XPP:MON:MMS:13', 'description': 'LOM Xtal2 Theta'},
    'ch2': {'prefix': 'XPP:MON:MMS:14', 'description': 'LOM Xtal2 Chi'},
    'h2n': {'prefix': 'XPP:MON:MMS:15', 'description': 'LOM Xtal2 Hn'},
    'diode2': {'prefix': 'XPP:MON:MMS:21', 'description': 'LOM Xtal2 PIPS'},
    'th2f': {'prefix': 'XPP:MON:PIC:03', 'description': ''},
    'ch2f': {'prefix': 'XPP:MON:PIC:04', 'description': ''},
    # DIAGNOSTICS TOWER
    'dh': {'prefix': 'XPP:MON:MMS:16', 'description': 'LOM Dia H'},
    'dv': {'prefix': 'XPP:MON:MMS:17', 'description': 'LOM Dia V'},
    'dr': {'prefix': 'XPP:MON:MMS:19', 'description': 'LOM Dia Theta'},
    'df': {'prefix': 'XPP:MON:MMS:27', 'description': 'LOM Dia Filter Wheel'},
    'dd': {'prefix': 'XPP:MON:MMS:18', 'description': 'LOM Dia PIPS'},
    'yag_zoom': {'prefix': 'XPP:MON:CLZ:01', 'description': 'LOM Zoom'},
}


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
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class CHI2(InOutRecordPositioner):
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class H2N(InOutRecordPositioner):
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class Y1(InOutRecordPositioner):
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


class Y2(InOutRecordPositioner):
    states_list = ['C', 'Si']
    in_states = ['C', 'Si']
    out_states = []


def get_prefix(motor):
    try:
        return LODCM_MOTORS[motor]['prefix']
    except KeyError:
        logging.error('Could not get the value of %f', motor)


class CrystalTower1(BaseInterface, Device):
    """
    Crystal Tower 1.

    Has the Si and C crystals with 2 angles and 5 linear motions.

    Parameters
    ----------
    z1_prefix : str
        LOM Xtal1 Z motor prefix.

    x1_prefix : str
        LOM Xtal1 X motor prefix.

    y1_prefix : str
        LOM Xtal1 Y motor prefix.

    th1_prefix : str
        LOM Xtal1 Theta motor prefix.

    ch1_prefix : str
        LOM Xtal1 Chi motor prefix.

    h1n_m_prefix : str
        LOM Xtal1 Hn motor prefix. Normal to the crystal surface movement.

    h1p_prefix : str
        LOM Xtal1 Hp motor prefix. Paralel to the crystal surface movement.

    """
    h1n = FCpt(H1N, '{self._prefix}:H1N', kind='hinted')
    y1_state = FCpt(Y1, '{self._prefix}:Y1', kind='omitted')
    chi1_state = FCpt(CHI1, '{self._prefix}:CHI1', kind='omitted')
    # x, y, and z are on the base but not touched in normal operations
    z1 = FCpt(IMS, '{self._z1_prefix}', kind='normal', doc='LOM Xtal1 Z')
    x1 = FCpt(IMS, '{self._x1_prefix}', kind='normal', doc='LOM Xtal1 X')
    y1 = FCpt(IMS, '{self._y1_prefix}', kind='normal', doc='LOM Xtal1 Y')
    # theta movement
    th1 = FCpt(IMS, '{self._th1_prefix}', kind='normal', doc='LOM Xtal1 Theta')
    # chi movement
    ch1 = FCpt(IMS, '{self._ch1_prefix}', kind='normal', doc='LOM Xtal1 Chi')
    # normal to the crystal surface movement
    h1n_m = FCpt(IMS, '{self._h1n_m_prefix}', kind='normal',
                 doc='LOM Xtal1 Hn')
    # paralell to the crystal surface movement
    h1p = FCpt(IMS, '{self._h1p_prefix}', kind='normal', doc='LOM Xtal1 Hp')

    # pseudo positioners
    # th1_si = FCpt(PseudoSingleInterface, '{self._prefix}:TH1:OFF_Si',
    #               kind='normal', name='th1_silicon',
    #               doc='Th1 motor offset for Si')
    # th1_c = FCpt(PseudoSingleInterface, '{self._prefix}:TH1:OFF_C',
    #              kind='normal', name='th1_diamond',
    #              doc='Th1 motor offset for C')
    # z1_si = FCpt(PseudoSingleInterface, '{self._prefix}:Z1:OFF_Si',
    #              kind='normal', name='z1_silicon',
    #              doc='Z1 motor offset for Si')
    # z1_c = FCpt(PseudoSingleInterface, '{self._prefix}:Z1:OFF_C',
    #             kind='normal', name='z1_diamond',
    #             doc='Z1 motor offset for C')

    # reflection pvs
    diamond_reflection = FCpt(EpicsSignalRO, '{self._prefix}:T1C:REF',
                              kind='omitted',
                              doc='Tower 1 Diamond crystal reflection')
    silicon_reflection = FCpt(EpicsSignalRO, '{self._prefix}:T1Si:REF',
                              kind='omitted',
                              doc='Tower 1 Silicon crystal reflection')

    tab_component_names = True

    def __init__(self, prefix, z1_prefix, x1_prefix, y1_prefix, th1_prefix,
                 ch1_prefix, h1n_m_prefix, h1p_prefix, *args, **kwargs):
        self._z1_prefix = z1_prefix
        self._x1_prefix = x1_prefix
        self._y1_prefix = y1_prefix
        self._th1_prefix = th1_prefix
        self._ch1_prefix = ch1_prefix
        self._h1n_m_prefix = h1n_m_prefix
        self._h1p_prefix = h1p_prefix
        self._prefix = prefix
        super().__init__('', *args, **kwargs)

    def is_diamond(self):
        """Check if tower 1 is with Diamond (C) material."""
        return (
            (self.h1n.position == 'C' or self.h1n.position == 'OUT') and
            self.y1_state.position == 'C' and
            self.chi1_state.position == 'C'
        )

    def is_silicon(self):
        """Check if tower 1 is with Silicon (Si) material."""
        return (
            (self.h1n.position == 'Si' or self.h1n.position == 'OUT') and
            self.y1_state.position == 'Si' and
            self.chi1_state.position == 'Si'
        )

    def get_reflection(self):
        """Get crystal's reflection."""
        if self.is_diamond():
            reflection = self.diamond_reflection.get()
        elif self.is_silicon():
            reflection = self.silicon_reflection.get()

        if reflection is None:
            raise ValueError('Unable to determine the crystal reflection')
        return reflection

    def get_material(self):
        """Get the current material."""
        if self.is_diamond():
            return 'C'
        elif self.is_silicon():
            return 'Si'


class CrystalTower1Init(CrystalTower1):
    """Helper initializing function for CrystalTower1 object."""
    def __init__(self, *args, parent, **kwargs):
        self._z1_prefix = parent._z1_prefix
        self._x1_prefix = parent._x1_prefix
        self._y1_prefix = parent._y1_prefix
        self._th1_prefix = parent._th1_prefix
        self._ch1_prefix = parent._ch1_prefix
        self._h1n_m_prefix = parent._h1n_m_prefix
        self._h1p_prefix = parent._h1p_prefix
        self._prefix = parent._prefix
        super().__init__(*args, parent=parent, z1_prefix=self._z1_prefix,
                         x1_prefix=self._x1_prefix, y1_prefix=self._y1_prefix,
                         th1_prefix=self._th1_prefix,
                         ch1_prefix=self._ch1_prefix,
                         h1n_m_prefix=self._h1n_m_prefix,
                         h1p_prefix=self._h1n_m_prefix,
                         prefix=self._prefix,
                         **kwargs)


class CrystalTower2(BaseInterface, Device):
    """
    Crystal Tower 2.

    Has the second Si and C crystals and a diode behind the crystals.

    Parameters
    ----------
    z2_prefix : str
        LOM Xtal2 Z motor prefix.

    x2_prefix : str
        LOM Xtal2 X motor prefix.

    y2_prefix : str
        LOM Xtal2 Y motor prefix.

    th2_prefix : str
        LOM Xtal2 Theta motor prefix.

    ch2_prefix : str
        LOM Xtal2 Chi motor prefix.

    h2n_prefix : str
        LOM Xtal2 Hn motor prefix.

    diode2_prefix : str
        LOM Xtal2 PIPS motor prefix.
    """
    h2n_state = FCpt(H2N, '{self._prefix}:H2N', kind='hinted')
    y2_state = FCpt(Y2, '{self._prefix}:Y2', kind='omitted')
    chi2_state = FCpt(CHI2, '{self._prefix}:CHI2', kind='omitted')
    # x, y, and z are on the base but not touched in normal operations
    z2 = FCpt(IMS, '{self._z2_prefix}', kind='normal', doc='LOM Xtal2 Z')
    x2 = FCpt(IMS, '{self._x2_prefix}', kind='normal', doc='LOM Xtal2 X')
    y2 = FCpt(IMS, '{self._y2_prefix}', kind='normal', doc='LOM Xtal2 Y')
    # thata movement
    th2 = FCpt(IMS, '{self._th2_prefix}', kind='normal', doc='LOM Xtal2 Theta')
    # chi movement
    ch2 = FCpt(IMS, '{self._ch2_prefix}', kind='normal', doc='LOM Xtal2 Chi')
    # normal to the crystal surface movement
    h2n = FCpt(IMS, '{self._h2n_prefix}', kind='normal', doc='LOM Xtal2 Hn')
    # in the DAQ for scanning in python
    diode2 = FCpt(IMS, '{self._diode2_prefix}',
                  kind='normal', doc='LOM Xtal2 PIPS')

    # pseudo positioners
    # th2_si = FCpt(PseudoSingleInterface, '{self._prefix}:TH2:OFF_Si',
    #               kind='normal', name='th2_silicon',
    #               doc='Th2 motor offset for Si')
    # th2_c = FCpt(PseudoSingleInterface, '{self._prefix}:TH2:OFF_C',
    #              kind='normal', name='th2_diamond',
    #              doc='Th2 motor offset for C')
    # z2_si = FCpt(PseudoSingleInterface, '{self._prefix}:Z2:OFF_Si',
    #              kind='normal', name='z1_diamond',
    #              doc='Z2 motor offset for Si')
    # z2_c = FCpt(PseudoSingleInterface, '{self._prefix}:Z2:OFF_C',
    #             kind='normal', name='z1_diamond',
    #             doc='Z2 motor offset for C')

    # reflection pvs
    diamond_reflection = FCpt(EpicsSignalRO, '{self._prefix}:T2C:REF',
                              kind='omitted',
                              doc='Tower 2 Diamond crystal reflection')
    silicon_reflection = FCpt(EpicsSignalRO, '{self._prefix}:T2Si:REF',
                              kind='omitted',
                              doc='Tower 2 Silicon crystal reflection')

    tab_component_names = True

    def __init__(self, prefix, z2_prefix, x2_prefix, y2_prefix, th2_prefix,
                 ch2_prefix, h2n_prefix, diode2_prefix, *args, **kwargs):
        self._z2_prefix = z2_prefix
        self._x2_prefix = x2_prefix
        self._y2_prefix = y2_prefix
        self._th2_prefix = th2_prefix
        self._ch2_prefix = ch2_prefix
        self._h2n_prefix = h2n_prefix
        self._diode2_prefix = diode2_prefix
        self._prefix = prefix
        super().__init__('', *args, **kwargs)

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
        """Get crystal's reflection."""
        if self.is_diamond():
            reflection = self.diamond_reflection.get()
        elif self.is_silicon():
            reflection = self.silicon_reflection.get()

        if reflection is None:
            raise ValueError('Unable to determine the crystal reflection')
        return reflection

    def get_material(self):
        """Get the current material."""
        if self.is_diamond():
            return 'C'
        elif self.is_silicon():
            return 'Si'


class CrystalTower2Init(CrystalTower2):
    """Helper initializing function for CrystalTower2 object."""
    def __init__(self, *args, parent, **kwargs):
        self._z2_prefix = parent._z2_prefix
        self._x2_prefix = parent._x2_prefix
        self._y2_prefix = parent._y2_prefix
        self._th2_prefix = parent._th2_prefix
        self._ch2_prefix = parent._ch2_prefix
        self._h2n_prefix = parent._h2n_prefix
        self._diode2_prefix = parent._diode2_prefix
        self._prefix = parent._prefix
        super().__init__(*args, parent=parent, z2_prefix=self._z2_prefix,
                         x2_prefix=self._x2_prefix, y2_prefix=self._y2_prefix,
                         th2_prefix=self._th2_prefix,
                         ch2_prefix=self._ch2_prefix,
                         h2n_prefix=self._h2n_prefix,
                         diode2_prefix=self._diode2_prefix,
                         prefix=self._prefix,
                         **kwargs)


class DiagnosticsTower(BaseInterface, Device):
    """
    Diagnostic Tower.

    Parameters
    ----------
    dh_prefix : str
        LOM Dia H motor prefix.

    dv_prefix : str
        LOM Dia V motor prefix.

    dr_prefix : str
        LOM Dia Theta motor prefix.

    df_prefix : str
        LOM Dia Filter Wheel motor prefix.

    dd_prefix : str
        LOM Dia PIPS motor prefix.

    yag_zoom_prefix : str
        LOM Zoom motor prefix.
    """
    # Located midway between T1 and T2 in the center of rotation of the device.
    # horizontal slits
    dh = FCpt(IMS, '{self._dh_prefix}', kind='normal', doc='LOM Dia H')
    # vertical slits
    dv = FCpt(IMS, '{self._dv_prefix}', kind='normal', doc='LOM Dia V')
    dr = FCpt(IMS, '{self._dr_prefix}', kind='normal', doc='LOM Dia Theta')
    # filters wheel
    df = FCpt(IMS, '{self._df_prefix}', kind='normal',
              doc='LOM Dia Filter Wheel')
    # pips diode
    dd = FCpt(IMS, '{self._dd_prefix}', kind='normal', doc='LOM Dia PIPS')
    # yag screen
    yag_zoom = FCpt(IMS, '{self._yag_zoom_prefix}', kind='normal',
                    doc='LOM Zoom')

    tab_component_names = True

    def __init__(self, dh_prefix, dv_prefix, dr_prefix, df_prefix,
                 dd_prefix, yag_zoom_prefix, * args, **kwargs):
        self._dh_prefix = dh_prefix
        self._dv_prefix = dv_prefix
        self._dr_prefix = dr_prefix
        self._df_prefix = df_prefix
        self._dd_prefix = dd_prefix
        self._yag_zoom_prefix = yag_zoom_prefix
        super().__init__('', *args, **kwargs)


class DiagnosticsTowerInit(DiagnosticsTower):
    """Helper initializing function for DiagnosticsTower object."""
    def __init__(self, *args, parent, **kwargs):
        self._dh_prefix = parent._dh_prefix
        self._dv_prefix = parent._dv_prefix
        self._dr_prefix = parent._dr_prefix
        self._df_prefix = parent._df_prefix
        self._dd_prefix = parent._dd_prefix
        self._yag_zoom_prefix = parent._yag_zoom_prefix
        super().__init__(*args, parent=parent, dh_prefix=self._dh_prefix,
                         dv_prefix=self._dv_prefix, dr_prefix=self._dr_prefix,
                         df_prefix=self._df_prefix, dd_prefix=self._dd_prefix,
                         yag_zoom_prefix=self._yag_zoom_prefix,
                         **kwargs)


class LODCM(BaseInterface, PseudoPositioner, Device):
    """
    Large Offset Dual Crystal Monochromator.

    This is the device that allows XPP and XCS to multiplex with downstream
    hutches. It contains two crystals that steer/split the beam and a number of
    diagnostic devices between them. Beam can continue onto the main line, onto
    the mono line, onto both, or onto neither.

    This positioner only considers the h1n and diagnostic motors.

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

    z1_prefix : str
        LOM Xtal1 Z motor prefix.

    x1_prefix : str
        LOM Xtal1 X motor prefix.

    y1_prefix : str
        LOM Xtal1 Y motor prefix.

    th1_prefix : str
        LOM Xtal1 Theta motor prefix.

    ch1_prefix : str
        LOM Xtal1 Chi motor prefix.

    h1n_m_prefix : str
        LOM Xtal1 Hn motor prefix. Normal to the crystal surface movement.

    h1p_prefix : str
        LOM Xtal1 Hp motor prefix. Paralel to the crystal surface movement.

    z2_prefix : str
        LOM Xtal2 Z motor prefix.

    x2_prefix : str
        LOM Xtal2 X motor prefix.

    y2_prefix : str
        LOM Xtal2 Y motor prefix.

    th2_prefix : str
        LOM Xtal2 Theta motor prefix.

    ch2_prefix : str
        LOM Xtal2 Chi motor prefix.

    h2n_prefix : str
        LOM Xtal2 Hn motor prefix.

    diode2_prefix : str
        LOM Xtal2 PIPS motor prefix.

    dh_prefix : str
        LOM Dia H motor prefix.

    dv_prefix : str
        LOM Dia V motor prefix.

    dr_prefix : str
        LOM Dia Theta motor prefix.

    df_prefix : str
        LOM Dia Filter Wheel motor prefix.

    dd_prefix : str
        LOM Dia PIPS motor prefix.

    yag_zoom_prefix : str
        LOM Zoom motor prefix.
    """
    h1n = Cpt(H1N, ':H1N', kind='hinted')
    yag = Cpt(YagLom, ":DV", kind='omitted')
    dectris = Cpt(Dectris, ":DH", kind='omitted')
    diode = Cpt(Diode, ":DIODE", kind='omitted')
    foil = Cpt(Foil, ":FOIL", kind='omitted')
    # y1_state = Cpt(Y1, ':Y1', kind='omitted')
    # chi1_state = Cpt(CHI1, ':CHI1', kind='omitted')
    # h2n_state = Cpt(H2N, ':H2N', kind='omitted')
    # y2_state = Cpt(Y2, ':Y2', kind='omitted')
    # chi2_state = Cpt(CHI2, ':CHI2', kind='omitted')
    # TODO energy component??
    # energy = Cpt(PseudoSingleInterface, egu='keV', limits=(4, 25))
    # vernier = Cpt(PseudoSingleInterface, egu='keV')
    # energy_c = Cpt(PseudoSingleInterface, egu='keV')
    # energy_si = Cpt(PseudoSingleInterface, egu='keV')

    first_tower = Cpt(CrystalTower1Init, name='T1', kind='normal')
    second_tower = Cpt(CrystalTower2Init, name='T2', kind='normal')
    diagnostic_tower = Cpt(DiagnosticsTowerInit, name='DT', kind='normal')

    # pseudo positioners
    th1_si = Cpt(PseudoSingleInterface, ':TH1:OFF_Si', kind='normal',
                 name='th1_silicon', doc='Th1 motor offset for Si')
    th1_c = Cpt(PseudoSingleInterface, ':TH1:OFF_C', kind='normal',
                name='th1_diamond', doc='Th1 motor offset for C')
    th2_si = Cpt(PseudoSingleInterface, ':TH2:OFF_Si', kind='normal',
                 name='th2_silicon', doc='Th2 motor offset for Si')
    th2_c = Cpt(PseudoSingleInterface, ':TH2:OFF_C', kind='normal',
                name='th2_diamond', doc='Th2 motor offset for C')
    z1_si = Cpt(PseudoSingleInterface, ':Z1:OFF_Si', kind='normal',
                name='z1_silicon', doc='Z1 motor offset for Si')
    z1_c = Cpt(PseudoSingleInterface, ':Z1:OFF_C', kind='normal',
               name='z1_diamond', doc='Z1 motor offset for C')
    z2_si = Cpt(PseudoSingleInterface, ':Z2:OFF_Si', kind='normal',
                name='z1_diamond', doc='Z2 motor offset for Si')
    z2_c = Cpt(PseudoSingleInterface, ':Z2:OFF_C', kind='normal',
               name='z1_diamond', doc='Z2 motor offset for C')

    # QIcon for UX
    _icon = 'fa.share-alt-square'

    tab_whitelist = ['h1n', 'yag', 'dectris', 'diode', 'foil', 'remove_dia']

    def __init__(self, prefix, *, name, z1_prefix=None, x1_prefix=None,
                 y1_prefix=None, th1_prefix=None, ch1_prefix=None,
                 h1n_m_prefix=None, h1p_prefix=None, z2_prefix=None,
                 x2_prefix=None, y2_prefix=None, th2_prefix=None,
                 ch2_prefix=None, h2n_prefix=None, diode2_prefix=None,
                 dh_prefix=None, dv_prefix=None, dr_prefix=None,
                 df_prefix=None, dd_prefix=None, yag_zoom_prefix=None,
                 main_line='MAIN', mono_line='MONO', **kwargs):
        self._prefix = prefix
        # tower 1
        self._z1_prefix = kwargs.get('z1_prefix') or get_prefix('z1')
        self._x1_prefix = kwargs.get('x1_prefix') or get_prefix('x1')
        self._y1_prefix = kwargs.get('y1_prefix') or get_prefix('y1')
        self._th1_prefix = kwargs.get('th1_prefix') or get_prefix('th1')
        self._ch1_prefix = kwargs.get('ch1_prefix') or get_prefix('ch1')
        self._h1n_m_prefix = (kwargs.get('h1n_m_prefix') or
                              get_prefix('h1n_m'))
        self._h1p_prefix = kwargs.get('h1p_prefix') or get_prefix('h1p')
        # tower 2
        self._z2_prefix = kwargs.get('z2_prefix') or get_prefix('z2')
        self._x2_prefix = kwargs.get('x2_prefix') or get_prefix('x2')
        self._y2_prefix = kwargs.get('y2_prefix') or get_prefix('y2')
        self._th2_prefix = kwargs.get('th2_prefix') or get_prefix('th2')
        self._ch2_prefix = kwargs.get('ch2_prefix') or get_prefix('ch2')
        self._h2n_prefix = kwargs.get('h2n_prefix') or get_prefix('h2n')
        self._diode2_prefix = (kwargs.get('diode2_prefix') or
                               get_prefix('diode2'))
        # Diagnostic Tower
        self._dh_prefix = kwargs.get('dh_prefix') or get_prefix('dh')
        self._dv_prefix = kwargs.get('dv_prefix') or get_prefix('dv')
        self._dr_prefix = kwargs.get('dr_prefix') or get_prefix('dr')
        self._df_prefix = kwargs.get('df_prefix') or get_prefix('df')
        self._dd_prefix = kwargs.get('dd_prefix') or get_prefix('dd')
        self._yag_zoom_prefix = (kwargs.get('yag_zoom_prefix') or
                                 get_prefix('yag_zoom'))
        super().__init__(prefix, name=name, **kwargs)
        self.main_line = main_line
        self.mono_line = mono_line
        # first tower
        self.z1 = self.first_tower.z1
        self.x1 = self.first_tower.x1
        self.y1 = self.first_tower.y1
        self.th1 = self.first_tower.th1
        self.ch1 = self.first_tower.ch1
        self.h1n_m = self.first_tower.h1n_m
        self.h1p = self.first_tower.h1p
        # second tower
        self.z2 = self.second_tower.z2
        self.x2 = self.second_tower.x2
        self.y2 = self.second_tower.y2
        self.th2 = self.second_tower.th2
        self.ch2 = self.second_tower.ch2
        self.h2n = self.second_tower.h2n
        self.diode2 = self.second_tower.diode2
        # diagnostic tower
        self.dh = self.diagnostic_tower.dh
        self.dv = self.diagnostic_tower.dv
        self.dr = self.diagnostic_tower.dr
        self.df = self.diagnostic_tower.df
        self.dd = self.diagnostic_tower.dd
        self.yag_zoom = self.diagnostic_tower.yag_zoom

    @property
    def inserted(self):
        """Returns `True` if either h1n crystal is in."""
        return self.h1n.inserted

    @property
    def removed(self):
        """Returns `True` if neither h1n crystal is in."""
        return self.h1n.removed

    def remove(self, moved_cb=None, timeout=None, wait=False):
        """Moves the h1n crystal out of the beam."""
        return self.h1n.remove(moved_cb=moved_cb, timeout=timeout, wait=wait)

    @property
    def transmission(self):
        """Returns h1n's transmission value."""
        return self.h1n.transmission

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

        if self.h1n.position == 'OUT':
            dest = [self.main_line]
        elif self.h1n.position == 'Si':
            dest = [self.mono_line]
        elif self.h1n.position == 'C':
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

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """
        Calculate a RealPosition from a given PseudoPosition.
        """
        # def moveE1(self, E, ID=None, reflection=None, tweak=False):
        # if reflection is None:
        #     # try to determine possible current reflection
        #reflection = self.get_tower1_reflection(astuple=True, check=True)
        #one of the theta motors to set what the energy is
        energy = self.get_energy() # - this gives me the wavelength
        return self.RealPosition(th1=energy)

    @real_position_argument
    def inverse(self, real_pos):
        """Calculate a PseudoPosition from a given RealPosition."""
        # th, z, material = self.calc_energy(energy=9000, material='Si', reflection=(1,1,1))
        # TODO: what energy should i use here?
        # set() 
        print(real_pos)
        th, z, material = self.calc_energy(self.th1.position)
        if material == "Si":
            return self.PseudoPosition(th1_si=th, th2_si=th, z1_si=-z, z2_si=z,
                                       th1_c=None, th2_c=None, z2_c=None,
                                       z1_c=None)
        elif material == "C":
            return self.PseudoPosition(th1_c=th, th2_c=th, z1_c=-z, z2_c=z,
                                       th1_si=None, th2_si=None, z1_si=None,
                                       z2_si=None, energy=None)
        else:
            raise ValueError("Invalid material ID: %s" % material)

    def get_reflection(self):
        """Get the crystal reflection"""
        ref_1 = self.first_tower.get_reflection()
        ref_2 = self.second_tower.get_reflection()
        if ref_1 != ref_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s',
                           ref_1, ref_2)
            raise ValueError('Invalid Crystal Arrangement')
        return ref_1

    def get_material(self):
        """Get the current crystals material."""
        m_1 = self.first_tower.get_material()
        m_2 = self.second_tower.get_material()
        if m_1 != m_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s', m_1, m_2)
            raise ValueError('Invalid Crystal Arrangement.')
        return m_1

    def calc_energy(self, energy, material=None, reflection=None):
        if reflection is None:
            # try to determine possible current reflection
            reflection = self.get_reflection(as_tuple=True, check=True)
        if material is None:
            # try to determine possible current material ID
            material = self.get_material(check=True)
        (th, z) = diffraction.get_lom_geometry(energy, material, reflection)
        return (th, z, material)

    def get_first_tower_energy(self, material=None, reflection=None):
        """
        Get photon energy for first tower in keV.

        Parameters
        ----------
        material : str, optional
            Chemical formula. E.g.: `Si`.
        reflection : tuple, optional
            Reflection of material. E.g.: `(1, 1, 1)`

        Returns
        -------
        energy : number
            Photon energy in keV.
        """
        if reflection is None:
            # try to determine possible current reflection
            reflection = self.get_first_tower_reflection(as_tuple=True,
                                                         check=True)
        if material is None:
            # try to determine possible current material id
            material = self.get_first_tower_material(check=True)
        if material == "Si":
            th = self.th1_si.wm()
        elif material == "C":
            th = self.th1_c.wm()
        else:
            raise ValueError("Invalid material Id: %s" % material)
        length = 2 * np.sin(np.deg2rad(th)) * diffraction.d_space(
            material, reflection)
        return diffraction.wavelength_to_energy(length) / 1000

    def get_second_tower_energy(self, material=None, reflection=None):
        """
        Get photon energy for second tower in keV.

        Parameters
        ----------
        material : str, optional
            Chemical formula. E.g.:`Si`.
        reflection : tuple, optional
            Reflection of material. E.g.: `(1, 1, 1)`

        Returns
        -------
        energy : number
            Photon Energy in eV.
        """
        if reflection is None:
            # try to determine possible current reflection
            reflection = self.second_tower.get_reflection()
        if material is None:
            # try to determine possible current material ID
            material = self.second_tower.get_material()
        if material == "Si":
            th = self.th2_si.wm()
        elif material == "C":
            th = self.th2_c.wm()
        else:
            raise ValueError("Invalid material ID: %s" % material)
        # th = self.th2.wm()
        length = 2 * np.sin(np.deg2rad(th)) * diffraction.d_space(
            material, reflection)
        return diffraction.wavelength_to_energy(length) / 1000

    def get_energy(self, material=None, reflection=None):
        """
        Get the Photon Energy. Energy is determined by the first crystal.
        TODO: why is energy determined by the first crystal?
        """
        return self.get_first_tower_energy(material, reflection)

    # @pseudo_position_argument
    # def move(self, position, wait=True, timeout=None, moved_cb=None):
    #     """
    #     Move to a specified position, optionally waiting for motion to
    #     complete.
    #     Checks for the motor step, and ask the user for confirmation if
    #     movement step is greater than default one.
    #     """
    #     if reflection is None:
    #         # try to determine possible current reflection
    #         reflection = self.get_t1_reflection(astuple=True, check=True)
    #     if ID is None:
    #         # try to determine possible current material ID
    #         ID = self.get_t1_material(check=True)
    #     (th, z) = self.getLomGeom(E, ID, reflection)
    #     if ID == "Si":
    #         self.th1Si.move_silent(th)
    #         if not tweak:
    #             self.dr.move_silent(2 * th)
    #         self.z1Si.move_silent(-z)
    #     elif ID == "C":
    #         self.th1C.move_silent(th)
    #         if not tweak:
    #             self.dr.move_silent(2 * th)
    #         self.z1C.move_silent(-z)
    #     else:
    #         raise ValueError("Invalid material ID: %s" % ID)

    def format_status_info(self, status_info):
        """Override status info handler to render the lodcm."""
        hutch = ''
        if 'XPP' in self.prefix:
            hutch = 'XPP '
        elif 'XCS' in self.prefix:
            hutch = 'XCS '

        material = self.get_material()
        if material == 'C':
            configuration = 'Diamond'
        elif material == 'Si':
            configuration = 'Silicon'
        else:
            configuration = 'Unknown'

        try:
            energy = self.get_energy()
        except Exception:
            energy = 'Unknown'

        ref = self.get_reflection()

        # tower 1
        z_units = get_status_value(
            status_info, 'first_tower', 'z1', 'user_setpoint', 'units')
        z_user = get_status_float(
            status_info, 'first_tower', 'z1', 'position')
        z_dial = get_status_float(
            status_info, 'first_tower', 'z1', 'dial_position', 'value')

        x_units = get_status_value(
            status_info, 'first_tower', 'x1', 'user_setpoint', 'units')
        x_user = get_status_float(status_info, 'first_tower', 'x1', 'position')
        x_dial = get_status_float(
            status_info, 'first_tower', 'x1', 'dial_position', 'value')

        th_units = get_status_value(
            status_info, 'first_tower', 'th1', 'user_setpoint', 'units')
        th_user = get_status_float(
            status_info, 'first_tower', 'th1', 'position')
        th_dial = get_status_float(
            status_info, 'first_tower', 'th1', 'dial_position', 'value')

        chi_units = get_status_value(
            status_info, 'first_tower', 'ch1', 'user_setpoint', 'units')
        chi_user = get_status_float(
            status_info, 'first_tower', 'ch1', 'position')
        chi_dial = get_status_float(
            status_info, 'first_tower', 'ch1', 'dial_position', 'value')

        y_units = get_status_value(
            status_info, 'first_tower', 'y1', 'user_setpoint', 'units')
        y_user = get_status_float(
            status_info, 'first_tower', 'y1', 'position')
        y_dial = get_status_float(
            status_info, 'first_tower', 'y1', 'dial_position', 'value')

        hn_units = get_status_value(
            status_info, 'first_tower', 'h1n_m', 'user_setpoint', 'units')
        hn_user = get_status_float(
            status_info, 'first_tower', 'h1n_m', 'position')
        hn_dial = get_status_float(
            status_info, 'first_tower', 'h1n_m', 'dial_position', 'value')

        hp_units = get_status_value(
            status_info, 'first_tower', 'h1p', 'user_setpoint', 'units')
        hp_user = get_status_float(
            status_info, 'first_tower', 'h1p', 'position')
        hp_dial = get_status_float(
            status_info, 'first_tower', 'h1p', 'dial_position', 'value')

        diode_units = get_status_value(
            status_info, 'first_tower', 'diode2', 'user_setpoint', 'units')
        diode_user = get_status_float(
            status_info, 'first_tower', 'diode', 'position')
        diode_dial = get_status_float(
            status_info, 'first_tower', 'diode', 'dial_position', 'value')
        # tower 2
        z2_user = get_status_float(
            status_info, 'second_tower', 'z2', 'position')
        z2_dial = get_status_float(
            status_info, 'second_tower', 'z2', 'dial_position', 'value')

        x2_user = get_status_float(
            status_info, 'second_tower', 'x2', 'position')
        x2_dial = get_status_float(
            status_info, 'second_tower', 'x2', 'dial_position', 'value')

        th2_user = get_status_float(
            status_info, 'second_tower', 'th2', 'position')
        th2_dial = get_status_float(
            status_info, 'second_tower', 'th2', 'dial_position', 'value')

        chi2_user = get_status_float(
            status_info, 'second_tower', 'ch2', 'position')
        chi2_dial = get_status_float(
            status_info, 'second_tower', 'ch2', 'dial_position', 'value')

        y2_user = get_status_float(
            status_info, 'second_tower', 'y2', 'position')
        y2_dial = get_status_float(
            status_info, 'second_tower', 'y2', 'dial_position', 'value')

        hn2_user = get_status_float(
            status_info, 'second_tower', 'h2n', 'position')
        hn2_dial = get_status_float(
            status_info, 'second_tower', 'h2n', 'dial_position', 'value')

        hp2_user = get_status_float(
            status_info, 'second_tower', 'h2p', 'position')
        hp2_dial = get_status_float(
            status_info, 'second_tower', 'h2p', 'dial_position', 'value')

        diode2_user = get_status_float(
            status_info, 'second_tower', 'diode2', 'position')
        diode2_dial = get_status_float(
            status_info, 'second_tower', 'diode2', 'dial_position', 'value')
        # diagnostics
        dh_units = get_status_value(
            status_info, 'diagnostic_tower', 'dh', 'user_setpoint', 'units')
        dh_user = get_status_float(
            status_info, 'diagnostic_tower', 'dh', 'position')
        dh_dial = get_status_float(
            status_info, 'diagnostic_tower', 'dh', 'dial_position', 'value')

        dv_units = get_status_value(
            status_info, 'diagnostic_tower', 'dv', 'user_setpoint', 'units')
        dv_user = get_status_float(
            status_info, 'diagnostic_tower', 'dv', 'position')
        dv_dial = get_status_float(
            status_info, 'diagnostic_tower', 'dv', 'dial_position', 'value')

        dr_units = get_status_value(
            status_info, 'diagnostic_tower', 'dr', 'user_setpoint', 'units')
        dr_user = get_status_float(
            status_info, 'diagnostic_tower', 'dr', 'position')
        dr_dial = get_status_float(
            status_info, 'diagnostic_tower', 'dr', 'dial_position', 'value')

        df_units = get_status_value(
            status_info, 'diagnostic_tower', 'df', 'user_setpoint', 'units')
        df_user = get_status_float(
            status_info, 'diagnostic_tower', 'df', 'position')
        df_dial = get_status_float(
            status_info, 'diagnostic_tower', 'df', 'dial_position', 'value')

        dd_units = get_status_value(
            status_info, 'diagnostic_tower', 'dd', 'user_setpoint', 'units')
        dd_user = get_status_float(
            status_info, 'diagnostic_tower', 'dd', 'position')
        dd_dial = get_status_float(
            status_info, 'diagnostic_tower', 'dd', 'dial_position', 'value')

        yag_zoom_units = get_status_value(status_info, 'diagnostic_tower',
                                          'yag_zoom', 'user_setpoint', 'units')
        yag_zoom_user = get_status_float(
            status_info, 'diagnostic_tower', 'yag_zoom', 'position')
        yag_zoom_dial = get_status_float(status_info, 'diagnostic_tower',
                                         'yag_zoom', 'dial_position', 'value')

        def form(left_str, center_str, right_str):
            return f'{left_str:<15}{center_str:>25}{right_str:>25}'

        return f"""\
{hutch}LODCM Motor Status Positions
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
{form(f'navitar [{yag_zoom_units}]',
      f'{yag_zoom_user} ({yag_zoom_dial})', '')}
"""
