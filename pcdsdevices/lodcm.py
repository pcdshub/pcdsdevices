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

from .doc_stubs import insert_remove
from .epics_motor import IMS
from .inout import InOutRecordPositioner
from .interface import BaseInterface, FltMvInterface
from .pseudopos import (PseudoPositioner, PseudoSingleInterface,
                        pseudo_position_argument, real_position_argument)
from .sim import FastMotor
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
    Crystal Tower 1.

    Has the Si and C crystals with 2 angles and 5 linear motions.
    `h1n_state` brings the crystal into the beam, moving horizontally
    (normal to the beam and parallel to the ground). It's also the only axis
    that can fully clear the crystal assembly from the beam. If h1n state is
    `OUT` and if we were to insert into the beam, we'd be aligned to the C
    crystal.
    `y1_state` brings the crystal into the beam, moving vertically
    (normal to the beam and normal to the ground)
    `chi1_state` rotates the crystal assembly.

    Parameters
    ----------
    prefix : str
        Epics base Pv prefix.
    """
    # x, y, and z are on the base but not touched in normal operations
    z1 = FCpt(IMS, '{self._m_prefix}:MON:MMS:04',
              kind='normal', doc='LOM Xtal1 Z')
    x1 = FCpt(IMS, '{self._m_prefix}:MON:MMS:05',
              kind='normal', doc='LOM Xtal1 X')
    y1 = FCpt(IMS, '{self._m_prefix}:MON:MMS:06',
              kind='normal', doc='LOM Xtal1 Y')
    # theta movement
    th1 = FCpt(IMS, '{self._m_prefix}:MON:MMS:07',
               kind='normal', doc='LOM Xtal1 Theta')
    # chi movement
    chi1 = FCpt(IMS, '{self._m_prefix}:MON:MMS:08',
                kind='normal', doc='LOM Xtal1 Chi')
    # normal to the crystal surface movement
    h1n = FCpt(IMS, '{self._m_prefix}:MON:MMS:09',
               kind='normal', doc='LOM Xtal1 Hn')
    # paralell to the crystal surface movement
    h1p = FCpt(IMS, '{self._m_prefix}:MON:MMS:20',
               kind='normal', doc='LOM Xtal1 Hp')

    # states
    h1n_state = Cpt(H1N, ':H1N', kind='hinted')
    y1_state = Cpt(Y1, ':Y1', kind='omitted')
    chi1_state = Cpt(CHI1, ':CHI1', kind='omitted')

    # reflection pvs
    diamond_reflection = Cpt(EpicsSignalRO, ':T1C:REF', kind='omitted',
                             doc='Tower 1 Diamond crystal reflection')
    silicon_reflection = Cpt(EpicsSignalRO, ':T1Si:REF', kind='omitted',
                             doc='Tower 1 Silicon crystal reflection')

    tab_component_names = True
    tab_whitelist = ['is_diamond', 'is_silicon', 'get_reflection',
                     'get_material']

    def __init__(self, prefix, *args, **kwargs):
        self._m_prefix = ''
        if 'XPP' in prefix:
            self._m_prefix = 'XPP'
        elif 'XCS' in prefix:
            self._m_prefix = 'HFX'
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

    def get_reflection(self, check=False):
        """Get crystal's reflection."""
        reflection = None
        if self.is_diamond():
            reflection = self.diamond_reflection.get()
        elif self.is_silicon():
            reflection = self.silicon_reflection.get()

        if check and reflection is None:
            raise ValueError('Unable to determine the crystal reflection')
        return reflection

    def get_material(self, check=False):
        """Get the current material."""
        if self.is_diamond():
            return 'C'
        elif self.is_silicon():
            return 'Si'
        if check:
            raise ValueError("Unable to determine crystal material")


class CrystalTower2(BaseInterface, Device):
    """
    Crystal Tower 2.

    Has the second Si and C crystals and a diode behind the crystals.

    Parameters
    ----------
    prefix : str
        Epics base Pv prefix.
    """
    # x, y, and z are on the base but not touched in normal operations
    z2 = FCpt(IMS, '{self._m_prefix}:MON:MMS:10',
              kind='normal', doc='LOM Xtal2 Z')
    x2 = FCpt(IMS, '{self._m_prefix}:MON:MMS:11',
              kind='normal', doc='LOM Xtal2 X')
    y2 = FCpt(IMS, '{self._m_prefix}:MON:MMS:12',
              kind='normal', doc='LOM Xtal2 Y')
    # thata movement
    th2 = FCpt(IMS, '{self._m_prefix}:MON:MMS:13',
               kind='normal', doc='LOM Xtal2 Theta')
    # chi movement
    chi2 = FCpt(IMS, '{self._m_prefix}:MON:MMS:14',
                kind='normal', doc='LOM Xtal2 Chi')
    # normal to the crystal surface movement
    h2n = FCpt(IMS, '{self._m_prefix}:MON:MMS:15',
               kind='normal', doc='LOM Xtal2 Hn')
    # in the DAQ for scanning in python, only used for commissioning
    diode2 = FCpt(IMS, '{self._m_prefix}:MON:MMS:21',
                  kind='normal', doc='LOM Xtal2 PIPS')

    # states
    h2n_state = Cpt(H2N, ':H2N', kind='hinted')
    y2_state = Cpt(Y2, ':Y2', kind='omitted')
    chi2_state = Cpt(CHI2, ':CHI2', kind='omitted')

    # reflection pvs
    diamond_reflection = Cpt(EpicsSignalRO, ':T2C:REF', kind='omitted',
                             doc='Tower 2 Diamond crystal reflection')
    silicon_reflection = Cpt(EpicsSignalRO, ':T2Si:REF', kind='omitted',
                             doc='Tower 2 Silicon crystal reflection')

    tab_component_names = True
    tab_whitelist = ['is_diamond', 'is_silicon', 'get_reflection',
                     'get_material']

    def __init__(self, prefix, *args, **kwargs):
        self._m_prefix = ''
        if 'XPP' in prefix:
            self._m_prefix = 'XPP'
        elif 'XCS' in prefix:
            self._m_prefix = 'HFX'
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

    def get_reflection(self, check=False):
        """Get crystal's reflection."""
        reflection = None
        if self.is_diamond():
            reflection = self.diamond_reflection.get()
        elif self.is_silicon():
            reflection = self.silicon_reflection.get()

        if check and reflection is None:
            raise ValueError('Unable to determine the crystal reflection')
        return reflection

    def get_material(self, check=False):
        """Get the current material."""
        if self.is_diamond():
            return 'C'
        elif self.is_silicon():
            return 'Si'
        if check:
            raise ValueError("Unable to determine crystal material")


class DiagnosticsTower(BaseInterface, Device):
    """
    Diagnostic Tower Motors.

    Parameters
    ----------
    prefix : str
        Epics base PV prefix.
    """
    # Located midway between T1 and T2 in the center of rotation of the device.
    # horizontal slits
    dh = Cpt(IMS, ':MON:MMS:16', kind='normal', doc='LOM Dia H')
    # vertical slits
    dv = Cpt(IMS, ':MON:MMS:17', kind='normal', doc='LOM Dia V')
    dr = Cpt(IMS, ':MON:MMS:19', kind='normal', doc='LOM Dia Theta')
    # filters wheel
    df = FCpt(IMS, '{self._prefix}:MON:MMS:{self._df_suffix}', kind='normal',
              doc='LOM Dia Filter Wheel')
    # pips diode
    dd = Cpt(IMS, ':MON:MMS:18', kind='normal', doc='LOM Dia PIPS')
    # yag screen
    yag_zoom = Cpt(IMS, ':MON:CLZ:01', kind='normal', doc='LOM Zoom')

    tab_component_names = True

    def __init__(self, prefix, *args, **kwargs):
        self._prefix = prefix
        self._df_suffix = '27'
        if 'XCS' in self._prefix:
            self._df_suffix = '22'
        super().__init__(prefix, *args, **kwargs)


class OffsetIMS(FltMvInterface, PseudoPositioner):
    """
    IMS motor with an offset.

    The driving idea for OffsetIMS is to let us separate the
    various unrelated PseudoPositioner-like things from the main class.
    Each different calculation can be independent, making it simpler to
    implement and maintain.
    """
    motor = FCpt(IMS, '{self._prefix}', kind='normal')
    offset = Cpt(PseudoSingleInterface, kind='normal')

    # TODO: fix this OffsetIMS !!!!

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        # for the given pseudo_pos, where should the motor be
        # TODO: what if this is none?
        motor_value = pseudo_pos.offset + self.motor.position
        return self.RealPosition(motor=motor_value)

    @real_position_argument
    def inverse(self, real_pos):
        real_pos = self.RealPosition(*real_pos)
        # for a given real_pos, where should the pseudo motor be
        offset = real_pos.motor - self.motor.position
        return self.PseudoPosition(offset=offset)

    def __init__(self, prefix, *args, **kwargs):
        self._prefix = prefix
        super().__init__(prefix, *args, **kwargs)


class LODCMEnergy(PseudoPositioner):
    # tower 1 states
    first_tower = FCpt(CrystalTower1, '{self._prefix}', kind='normal')
    second_tower = FCpt(CrystalTower2, '{self._prefix}', kind='normal')
    # we get the energy from theta1
    # th1 = FCpt(IMS, '{self._m_prefix}:MON:MMS:07',
    #            kind='normal', doc='LOM Xtal1 Theta')
    # offset positioners used to set the Energy
    th1_si = Cpt(OffsetIMS, ':TH1:OFF_Si', kind='normal', name='th1_si',
                 doc='Th1 motor offset for Si')
    th1_c = Cpt(OffsetIMS, ':TH1:OFF_C', kind='normal', name='th1_c',
                doc='Th1 motor offset for C')
    th2_si = Cpt(OffsetIMS, ':TH2:OFF_Si', kind='normal', name='th2_si',
                 doc='Th2 motor offset for Si')
    th2_c = Cpt(OffsetIMS, ':TH2:OFF_C', kind='normal', name='th2_c',
                doc='Th2 motor offset for C')
    z1_si = Cpt(OffsetIMS, ':Z1:OFF_Si', kind='normal', name='z1_si',
                doc='Z1 motor offset for Si')
    z1_c = Cpt(OffsetIMS, ':Z1:OFF_C', kind='normal', name='z1_c',
               doc='Z1 motor offset for C')
    z2_si = Cpt(OffsetIMS, ':Z2:OFF_Si', kind='normal', name='z1_si',
                doc='Z2 motor offset for Si')
    z2_c = Cpt(OffsetIMS, ':Z2:OFF_C', kind='normal', name='z1_c',
               doc='Z2 motor offset for C')
    # offset positioners
    # tower 1
    x1_c = Cpt(OffsetIMS, ':X1:OFF_C', kind='normal',
               name='x1_c', doc='X1 motor offset for C')
    x1_si = Cpt(OffsetIMS, ':X1:OFF_Si', kind='normal',
                name='x1_si', doc='X1 motor offset for Si')
    y1_c = Cpt(OffsetIMS, ':Y1:OFF_C', kind='normal',
               name='y1_c', doc='Y1 motor offset for C')
    y1_si = Cpt(OffsetIMS, ':Y1:OFF_Si', kind='normal',
                name='y1_si', doc='Y1 motor offset for Si')
    chi1_c = Cpt(OffsetIMS, ':CHI1:OFF_C', kind='normal',
                 name='chi1_c ', doc='Chi 1 motor offset for C')
    chi1_si = Cpt(OffsetIMS, ':CHI1:OFF_Si', kind='normal',
                  name='chi1_si', doc='Chi 1 motor offset for Si')
    h1n_c = Cpt(OffsetIMS, ':H1N:OFF_C', kind='normal',
                name='', doc='H1n motor offset for C')
    h1n_si = Cpt(OffsetIMS, ':H1N:OFF_Si', kind='normal',
                 name='h1n_si', doc='H1n motor offset for Si')
    h1p_c = Cpt(OffsetIMS, ':H1P:OFF_C', kind='normal',
                name='h1p_c', doc='H1p motor offset for C')
    h1p_si = Cpt(OffsetIMS, ':H1P:OFF_Si', kind='normal',
                 name='h1p_si', doc='H1p motor offset for Si')
    # tower 2
    x2_c = Cpt(OffsetIMS, ':X2:OFF_C', kind='normal',
               name='x2_c ', doc='X2 motor offset for C')
    x2_si = Cpt(OffsetIMS, ':X2:OFF_Si', kind='normal',
                name='x2_si', doc='X2 motor offset for Si')
    y2_c = Cpt(OffsetIMS, ':Y2:OFF_C', kind='normal',
               name='y2_c', doc='Y2 motor offset for C')
    y2_si = Cpt(OffsetIMS, ':Y2:OFF_Si', kind='normal',
                name='y2_si', doc='Y2 motor offset for Si')
    chi2_c = Cpt(OffsetIMS, ':CHI2:OFF_C', kind='normal',
                 name='chi2_c', doc='Chi 2 motor offset for C')
    chi2_si = Cpt(OffsetIMS, ':CHI2:OFF_Si', kind='normal',
                  name='chi2_si', doc='Chi 2 motor offset for Si')
    h2n_c = Cpt(OffsetIMS, ':H2N:OFF_C', kind='normal',
                name='h2n_c', doc=' H2n motor offset for C')
    h2n_si = Cpt(OffsetIMS, ':H2N:OFF_Si', kind='normal',
                 name='h2n_si', doc='H2n motor offset for Si')

    # energy pseudo positioner
    energy = Cpt(PseudoSingleInterface, egu='keV', kind='hinted',
                 limits=(5, 25))

    def __init__(self, prefix, *args, **kwargs):
        self._prefix = prefix
        self._m_prefix = ''
        if 'XPP' in self._prefix:
            self._m_prefix = 'XPP'
        elif 'XCS' in self._prefix:
            self._m_prefix = 'HFX'
        super().__init__(prefix=prefix, *args, **kwargs)

    def get_reflection(self, check=False):
        """Get the crystal reflection."""
        ref_1 = self.first_tower.get_reflection(check)
        ref_2 = self.second_tower.get_reflection(check)
        if ref_1 != ref_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s',
                           ref_1, ref_2)
            raise ValueError('Invalid Crystal Arrangement')
        return ref_1

    def get_material(self, check=False):
        """Get the current crystals material."""
        m_1 = self.first_tower.get_material()
        m_2 = self.second_tower.get_material()
        if m_1 != m_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s', m_1, m_2)
            raise ValueError('Invalid Crystal Arrangement.')
        return m_1

    def calc_energy(self, energy, material=None, reflection=None):
        """Calculate the lom geometry."""
        if reflection is None:
            # try to determine possible current reflection
            reflection = self.get_reflection(check=True)
        if material is None:
            # try to determine possible current material ID
            material = self.get_material(check=True)
        (th, z) = diffraction.get_lom_geometry(energy, material, reflection)
        return (th, z, material)

    def get_energy(self, material=None, reflection=None):
        """
        Get photon energy from first tower in keV.

        Energy is determined by the first crystal (Theta motor).

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
            reflection = self.first_tower.get_reflection(check=True)
        if material is None:
            # try to determine possible current material id
            material = self.first_tower.get_material(check=True)
        if material == "Si":
            th = self.th1_si.wm()
        elif material == "C":
            th = self.th1_c.wm()
        else:
            raise ValueError("Invalid material Id: %s" % material)
        length = 2 * np.sin(np.deg2rad(th)) * diffraction.d_space(
            material, reflection)
        return common.wavelength_to_energy(length) / 1000

    # @pseudo_position_argument
    # def forward(self, pseudo_pos):
    #     """Calculate a RealPosition from a given PseudoPosition."""
    #     energy = self.get_energy()
    #     return self.RealPosition(th1=energy)

    # @real_position_argument
    # def inverse(self, real_pos):
    #     """Calculate a PseudoPosition from a given RealPosition."""
    #     real_pos = self.RealPosition(*real_pos)
    #     th, z, material = self.calc_energy(real_pos.th1)
    #     if material == "Si":
    #         return self.PseudoPosition(th1_si=th, th2_si=th, z1_si=-z,
    #                                    z2_si=z)
    #     elif material == "C":
    #         return self.PseudoPosition(th1_c=th, th2_c=th, z1_c=-z, z2_c=z)
    #     else:
    #         raise ValueError("Invalid material ID: %s" % material)

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """Calculate a RealPosition from a given PseudoPosition."""
        # if my pseudo positioner is here,
        # this is where my real motor should be
        pseudo_pos = self.PseudoPosition(*pseudo_pos)
        th, z, material = self.calc_energy(pseudo_pos.energy)
        if material == "Si":
            return self.RealPosition(th1_si=th, th2_si=th, z1_si=-z, z2_si=z)
        elif material == "C":
            return self.RealPosition(th1_c=th, th2_c=th, z1_c=-z, z2_c=z)
        else:
            raise ValueError("Invalid material ID: %s" % material)

    @real_position_argument
    def inverse(self, real_pos):
        """Calculate a PseudoPosition from a given RealPosition."""
        # if my real motor is here,
        # this is where my pseudo positioner should be
        # real_pos = self.RealPosition(*real_pos)
        energy = self.get_energy()
        return self.PseudoPosition(energy=energy)
        # real_pos = self.RealPosition(*real_pos)
        # th, z, material = self.calc_energy(real_pos.th1)
        # if material == "Si":
        #     return self.PseudoPosition(th1_si=th, th2_si=th, z1_si=-z,
        #                                z2_si=z)
        # elif material == "C":
        #     return self.PseudoPosition(th1_c=th, th2_c=th, z1_c=-z, z2_c=z)
        # else:
        #     raise ValueError("Invalid material ID: %s" % material)


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
    #  h1n_state = Cpt(H1N, ':H1N', kind='hinted')
    yag = Cpt(YagLom, ":DV", kind='omitted')
    dectris = Cpt(Dectris, ":DH", kind='omitted')
    diode = Cpt(Diode, ":DIODE", kind='omitted')
    foil = Cpt(Foil, ":FOIL", kind='omitted')

    first_tower = FCpt(CrystalTower1, '{self._prefix}', name='T1',
                       kind='normal')
    second_tower = FCpt(CrystalTower2, '{self._prefix}', name='T2',
                        kind='normal')
    diagnostic_tower = FCpt(DiagnosticsTower, '{self._m_prefix}', name='DT',
                            kind='normal')
    calc = FCpt(LODCMEnergy, '{self._prefix}', kind='normal')

    # QIcon for UX
    _icon = 'fa.share-alt-square'

    tab_whitelist = ['h1n_state', 'yag', 'dectris', 'diode', 'foil',
                     'remove_dia', 'first_tower', 'second_tower',
                     'diagnostic_tower', 'calc']

    def __init__(self, prefix, *, name, main_line='MAIN', mono_line='MONO',
                 **kwargs):
        self._prefix = prefix
        self._m_prefix = ''
        if 'XPP' in self._prefix:
            self._m_prefix = 'XPP'
        elif 'XCS' in self._prefix:
            self._m_prefix = 'HFX'

        super().__init__(prefix, name=name, **kwargs)
        self.main_line = main_line
        self.mono_line = mono_line
        # first tower
        self.z1 = self.first_tower.z1
        self.x1 = self.first_tower.x1
        self.y1 = self.first_tower.y1
        self.th1 = self.first_tower.th1
        self.chi1 = self.first_tower.chi1
        self.h1n = self.first_tower.h1n
        self.h1p = self.first_tower.h1p
        # second tower
        self.z2 = self.second_tower.z2
        self.x2 = self.second_tower.x2
        self.y2 = self.second_tower.y2
        self.th2 = self.second_tower.th2
        self.chi2 = self.second_tower.chi2
        self.h2n = self.second_tower.h2n
        self.diode2 = self.second_tower.diode2
        # diagnostic tower
        self.dh = self.diagnostic_tower.dh
        self.dv = self.diagnostic_tower.dv
        self.dr = self.diagnostic_tower.dr
        self.df = self.diagnostic_tower.df
        self.dd = self.diagnostic_tower.dd
        self.yag_zoom = self.diagnostic_tower.yag_zoom
        self.energy = self.calc.energy
        # states
        self.h1n_state = self.first_tower.h1n_state
        self.y1_state = self.first_tower.y1_state
        self.chi1_state = self.first_tower.chi1_state
        self.h2n_state = self.second_tower.h2n_state
        self.y2_state = self.second_tower.y2_state
        self.chi2_state = self.second_tower.chi2_state
        # offset positioners - tower 1
        self.z1_c = self.calc.z1_c
        self.z1_si = self.calc.z1_si
        self.x1_c = self.calc.x1_c
        self.x1_si = self.calc.x1_si
        self.y1_c = self.calc.y1_c
        self.y1_si = self.calc.y1_si
        self.th1_c = self.calc.th1_c
        self.th1_si = self.calc.th1_si
        self.chi1_c = self.calc.chi1_c
        self.chi1_si = self.calc.chi1_si
        self.h1n_c = self.calc.h1n_c
        self.h1n_si = self.calc.h1n_si
        self.h1p_c = self.calc.h1p_c
        self.h1p_si = self.calc.h1p_si
        # offset positioners - tower 2
        self.z2_c = self.calc.z2_c
        self.z2_si = self.calc.z2_si
        self.x2_c = self.calc.x2_c
        self.x2_si = self.calc.x2_si
        self.y2_c = self.calc.y2_c
        self.y2_si = self.calc.y2_si
        self.th2_c = self.calc.th2_c
        self.th2_si = self.calc.th2_si
        self.chi2_c = self.calc.chi2_c
        self.chi2_si = self.calc.chi2_si
        self.h2n_c = self.calc.h2n_c
        self.h2n_si = self.calc.h2n_si

    @property
    def reflection(self):
        """Returns the current reflection."""
        return self.calc.get_reflection()

    @property
    def material(self):
        """Returns the current material in Towers."""
        return self.calc.get_material()

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

    def format_status_info(self, status_info):
        """Override status info handler to render the lodcm."""
        hutch = ''
        if 'XPP' in self.prefix:
            hutch = 'XPP '
        elif 'XCS' in self.prefix:
            hutch = 'XCS '

        try:
            material = self.material
        except Exception:
            material = 'Unknown'

        if material == 'C':
            configuration = 'Diamond'
        elif material == 'Si':
            configuration = 'Silicon'
        else:
            configuration = 'Unknown'

        try:
            energy = self.calc.get_energy()
        except Exception:
            energy = 'Unknown'

        try:
            ref = self.reflection
        except Exception:
            ref = 'Unknown'
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
            status_info, 'first_tower', 'chi1', 'user_setpoint', 'units')
        chi_user = get_status_float(
            status_info, 'first_tower', 'chi1', 'position')
        chi_dial = get_status_float(
            status_info, 'first_tower', 'chi1', 'dial_position', 'value')

        y_units = get_status_value(
            status_info, 'first_tower', 'y1', 'user_setpoint', 'units')
        y_user = get_status_float(
            status_info, 'first_tower', 'y1', 'position')
        y_dial = get_status_float(
            status_info, 'first_tower', 'y1', 'dial_position', 'value')

        hn_units = get_status_value(
            status_info, 'first_tower', 'h1n', 'user_setpoint', 'units')
        hn_user = get_status_float(
            status_info, 'first_tower', 'h1n', 'position')
        hn_dial = get_status_float(
            status_info, 'first_tower', 'h1n', 'dial_position', 'value')

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
            status_info, 'second_tower', 'chi2', 'position')
        chi2_dial = get_status_float(
            status_info, 'second_tower', 'chi2', 'dial_position', 'value')

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
        yag_zoom_user = get_status_float(status_info, 'diagnostic_tower',
                                         'yag_zoom', 'position', precision=0)
        yag_zoom_dial = get_status_float(status_info, 'diagnostic_tower',
                                         'yag_zoom', 'dial_position', 'value',
                                         precision=0)

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


class SIMOffsetIMS(OffsetIMS):
    """Simulation of OffsetIMS device for testing."""
    motor = Cpt(FastMotor, limits=(-100, 100))
