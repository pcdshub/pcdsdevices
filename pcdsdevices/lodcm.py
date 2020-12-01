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
from numbers import Number

from .component import UnrelatedComponent as UCpt
from .doc_stubs import insert_remove
from .inout import InOutRecordPositioner
from .interface import BaseInterface
from .epics_motor import IMS, Motor
from .sim import FastMotor
from .utils import get_status_value

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


LODCM_MOTORS = {
    # CRYSTAL TOWER ONE
    'z1': {'prefix': 'XPP:MON:MMS:04', 'description': 'LOM Xtal1 Z',
           'motor': Motor('XPP:MON:MMS:04', name='z1')},
    'x1': {'prefix': 'XPP:MON:MMS:05', 'description': 'LOM Xtal1 X',
           'motor': Motor('XPP:MON:MMS:05', name='x1')},
    'y1': {'prefix': 'XPP:MON:MMS:06', 'description': 'LOM Xtal1 Y',
           'motor': Motor('XPP:MON:MMS:06', name='y1')},
    'th1': {'prefix': 'XPP:MON:MMS:07', 'description': 'LOM Xtal1 Theta',
            'motor': Motor('XPP:MON:MMS:07', name='th1')},
    'ch1': {'prefix': 'XPP:MON:MMS:08', 'description': 'LOM Xtal1 Chi',
            'motor': Motor('XPP:MON:MMS:08', name='ch1')},
    'h1n_m': {'prefix': 'XPP:MON:MMS:09', 'description': 'LOM Xtal1 Hn',
              'motor': Motor('XPP:MON:MMS:09', name='h1n_m')},
    'h1p': {'prefix': 'XPP:MON:MMS:20', 'description': 'LOM Xtal1 Hp',
            'motor': Motor('XPP:MON:MMS:20', name='h1p')},
    'th1f': {'prefix': 'XPP:MON:PIC:01', 'description': '',
             'motor': Motor('XPP:MON:PIC:01', name='th1f')},
    'ch1f': {'prefix': 'XPP:MON:PIC:02', 'description': '',
             'motor': Motor('XPP:MON:PIC:02', name='ch1f')},
    # CRYSTAL TOWER TWO
    'z2': {'prefix': 'XPP:MON:MMS:10', 'description': 'LOM Xtal2 Z',
           'motor': Motor('XPP:MON:MMS:10', name='z2')},
    'x2': {'prefix': 'XPP:MON:MMS:11', 'description': 'LOM Xtal2 X',
           'motor': Motor('XPP:MON:MMS:11', name='x2')},
    'y2': {'prefix': 'XPP:MON:MMS:12', 'description': 'LOM Xtal2 Y',
           'motor': Motor('XPP:MON:MMS:12', name='y2')},
    'th2': {'prefix': 'XPP:MON:MMS:13', 'description': 'LOM Xtal2 Theta',
            'motor': Motor('XPP:MON:MMS:13', name='th2')},
    'ch2': {'prefix': 'XPP:MON:MMS:14', 'description': 'LOM Xtal2 Chi',
            'motor': Motor('XPP:MON:MMS:14', name='ch2')},
    'h2n': {'prefix': 'XPP:MON:MMS:15', 'description': 'LOM Xtal2 Hn',
            'motor': Motor('XPP:MON:MMS:15', name='h2n')},
    'diode2': {'prefix': 'XPP:MON:MMS:21', 'description': 'LOM Xtal2 PIPS',
               'motor': Motor('XPP:MON:MMS:21', name='diode2')},
    'th2f': {'prefix': 'XPP:MON:PIC:03', 'description': '',
             'motor': Motor('XPP:MON:PIC:03', name='th2f')},
    'ch2f': {'prefix': 'XPP:MON:PIC:04', 'description': '',
             'motor': Motor('XPP:MON:PIC:04', name='ch2f')},
    # DIAGNOSTICS TOWER
    'dh': {'prefix': 'XPP:MON:MMS:16', 'description': 'LOM Dia H',
           'motor': Motor('XPP:MON:MMS:16', name='dh')},
    'dv': {'prefix': 'XPP:MON:MMS:17', 'description': 'LOM Dia V',
           'motor': Motor('XPP:MON:MMS:17', name='dv')},
    'dr': {'prefix': 'XPP:MON:MMS:19', 'description': 'LOM Dia Theta',
           'motor': Motor('XPP:MON:MMS:19', name='dr')},
    'df': {'prefix': 'XPP:MON:MMS:27', 'description': 'LOM Dia Filter Wheel',
           'motor': Motor('XPP:MON:MMS:27', name='df')},
    'dd': {'prefix': 'XPP:MON:MMS:18', 'description': 'LOM Dia PIPS',
           'motor': Motor('XPP:MON:MMS:18', name='dd')},
    'yag_zoom': {'prefix': 'XPP:MON:CLZ:01', 'description': 'LOM Zoom',
                 'motor': Motor('XPP:MON:CLZ:01', name='yag_zoom')},
}


def get_prefix(motor):
    try:
        return LODCM_MOTORS[motor]['prefix']
    except KeyError:
        logging.error('Could not get the value of %f', motor)


class LODCM(BaseInterface, Device):
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
        LOM Xtal1 Hn motor prefix.

    h1p_prefix : str
        LOM Xtal1 Hp motor prefix.

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
    y1_state = Cpt(Y1, ':Y1', kind='omitted')
    chi1_state = Cpt(CHI1, ':CHI1', kind='omitted')
    h2n_state = Cpt(H2N, ':H2N', kind='omitted')
    y2_state = Cpt(Y2, ':Y2', kind='omitted')
    chi2_state = Cpt(CHI2, ':CHI2', kind='omitted')

    # Crystal Tower 1
    z1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 Z')
    x1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 X')
    y1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 Y')
    th1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 Theta')
    ch1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 Chi')
    h1n_m = UCpt(IMS, kind='normal', doc='LOM Xtal1 Hn')
    h1p = UCpt(IMS, kind='normal', doc='LOM Xtal1 Hp')
    # Crystal Tower 2
    z2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 Z')
    x2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 X')
    y2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 Y')
    th2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 Theta')
    ch2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 Chi')
    h2n = UCpt(IMS, kind='normal', doc='LOM Xtal2 Hn')
    diode2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 PIPS')
    # Diagnostic Tower
    dh = UCpt(IMS, kind='normal', doc='LOM Dia H')
    dv = UCpt(IMS, kind='normal', doc='LOM Dia V')
    dr = UCpt(IMS, kind='normal', doc='LOM Dia Theta')
    df = UCpt(IMS, kind='normal', doc='LOM Dia Filter Wheel')
    dd = UCpt(IMS, kind='normal', doc='LOM Dia PIPS')
    yag_zoom = UCpt(IMS, kind='normal', doc='LOM Zoom')

    t1_c_ref = Cpt(EpicsSignalRO, ':T1C:REF', kind='omitted',
                   doc='Tower 1 Diamond crystal reflection')
    t1_si_ref = Cpt(EpicsSignalRO, ':T1Si:REF', kind='omitted',
                    doc='Tower 1 Silicon crystal reflection')
    t2_c_ref = Cpt(EpicsSignalRO, ':T2C:REF', kind='omitted',
                   doc='Tower 2 Diamond crystal reflection')
    t2_si_ref = Cpt(EpicsSignalRO, ':T2Si:REF', kind='omitted',
                    doc='Tower 2 Silicon crystal reflection')

    # QIcon for UX
    _icon = 'fa.share-alt-square'

    tab_whitelist = ['h1n', 'yag', 'dectris', 'diode', 'foil',
                     'remove_dia']

    def __init__(self, prefix, *, name, main_line='MAIN', mono_line='MONO',
                 **kwargs):
        kwargs['z1_prefix'] = kwargs.get('z1_prefix') or get_prefix('z1')
        kwargs['x1_prefix'] = kwargs.get('x1_prefix') or get_prefix('z1')
        kwargs['y1_prefix'] = kwargs.get('y1_prefix') or get_prefix('y1')
        kwargs['th1_prefix'] = kwargs.get('th1_prefix') or get_prefix('th1')
        kwargs['ch1_prefix'] = kwargs.get('ch1_prefix') or get_prefix('ch1')
        kwargs['h1n_m_prefix'] = (kwargs.get('h1n_m_prefix') or
                                  get_prefix('h1n_m'))
        kwargs['h1p_prefix'] = kwargs.get('h1p_prefix') or get_prefix('h1p')
        # tower 2
        kwargs['z2_prefix'] = kwargs.get('z2_prefix') or get_prefix('z2')
        kwargs['x2_prefix'] = kwargs.get('x2_prefix') or get_prefix('x2')
        kwargs['y2_prefix'] = kwargs.get('y2_prefix') or get_prefix('y2')
        kwargs['th2_prefix'] = kwargs.get('th2_prefix') or get_prefix('th2')
        kwargs['ch2_prefix'] = kwargs.get('ch2_prefix') or get_prefix('ch2')
        kwargs['h2n_prefix'] = kwargs.get('h2n_prefix') or get_prefix('h2n')
        kwargs['diode2_prefix'] = kwargs.get(
            'diode2_prefix') or get_prefix('diode2')
        # Diagnostic Tower
        kwargs['dh_prefix'] = kwargs.get('dh_prefix') or get_prefix('dh')
        kwargs['dv_prefix'] = kwargs.get('dv_prefix') or get_prefix('dv')
        kwargs['dr_prefix'] = kwargs.get('dr_prefix') or get_prefix('dr')
        kwargs['df_prefix'] = kwargs.get('df_prefix') or get_prefix('df')
        kwargs['dd_prefix'] = kwargs.get('dd_prefix') or get_prefix('dd')
        kwargs['yag_zoom_prefix'] = kwargs.get(
            'yag_zoom_prefix') or get_prefix('yag_zoom')
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)
        self.main_line = main_line
        self.mono_line = mono_line

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

    def _is_tower_1_c(self):
        """Check if tower 1 is with Diamond (C) material."""
        return (
            (self.h1n.position == 'C' or self.h1n.position == 'OUT') and
            self.y1_state.position == 'C' and
            self.chi1_state.position == 'C'
        )

    def _is_tower_1_si(self):
        """Check if tower 1 is with Silicon (Si) material."""
        return (
            (self.h1n.position == 'Si' or self.h1n.position == 'OUT') and
            self.y1_state.position == 'Si' and
            self.chi1_state.position == 'Si'
        )

    def _is_tower_2_c(self):
        """Check if tower 2 is with Diamond (C) material."""
        return (self.h2n_state.position == 'C' and
                self.y2_state.position == 'C' and
                self.chi2_state.position == 'C')

    def _is_tower_2_si(self):
        """Check if tower 2 is with Silicon (Si) material."""
        return (self.h2n_state.position == 'Si' and
                self.y2_state.position == 'Si' and
                self.chi2_state.position == 'Si')

    def get_reflection(self, as_tuple, check):
        """Get the crystal reflection"""
        ref_1 = self._get_reflection(1, as_tuple=False, check=False)
        ref_2 = self._get_reflection(2, as_tuple=False, check=False)
        if ref_1 != ref_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s',
                           ref_1, ref_2)
            raise ValueError('Invalid Crystal Arrangement')
        return ref_1

    def _get_reflection(self, tower_num, as_tuple, check):
        refs = None
        ref = None
        if tower_num == 1:
            if self._is_tower_1_c():
                refs = self.t1_c_ref.get()
            elif self._is_tower_1_si():
                refs = self.t1_si_ref.get()
        elif tower_num == 2:
            if self._is_tower_2_c():
                refs = self.t2_c_ref.get()
            elif self._is_tower_2_si():
                refs = self.t2_si_ref.get()
        if check and refs is None:
            raise ValueError('Unable to determine the crystal reflection')
        if as_tuple:
            return refs
        else:
            if refs is not None:
                for r in refs:
                    if ref is None:
                        ref = str(r)
                    else:
                        ref += str(r)
            return ref

    def _get_material(self, tower_num, check):
        if tower_num == 1:
            if self._is_tower_1_c():
                return 'C'
            elif self._is_tower_1_si():
                return 'Si'
        elif tower_num == 2:
            if self._is_tower_2_c():
                return 'C'
            elif self._is_tower_2_si():
                return 'Si'
        if check:
            raise ValueError("Unable to determine crysta's material.")

    def get_material(self, check=False):
        m_1 = self._get_material(1, check=False)
        m_2 = self._get_material(2, check=False)
        if m_1 != m_2:
            logger.warning('Crystals do not match: c1: %s, c2: %s', m_1, m_2)
            raise ValueError('Invalid Crystal Arrangement.')
        return m_1

    remove_dia.__doc__ += insert_remove

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
        ref = self.get_reflection(as_tuple=True, check=False)
        # tower 1
        z_units = get_status_value(status_info, 'z1', 'user_setpoint', 'units')
        z_user = get_status_value(status_info, 'z1', 'position')
        z_dial = get_status_value(status_info, 'z1', 'dial_position', 'value')

        x_units = get_status_value(status_info, 'x1', 'user_setpoint', 'units')
        x_user = get_status_value(status_info, 'x1', 'position')
        x_dial = get_status_value(status_info, 'x1', 'dial_position', 'value')

        th_units = get_status_value(status_info, 'th1', 'user_setpoint',
                                    'units')
        th_user = get_status_value(status_info, 'th1', 'position')
        th_dial = get_status_value(status_info, 'th1', 'dial_position',
                                   'value')

        chi_units = get_status_value(status_info, 'ch1', 'user_setpoint',
                                     'units')
        chi_user = get_status_value(status_info, 'ch1', 'position')
        chi_dial = get_status_value(status_info, 'ch1', 'dial_position',
                                    'value')

        y_units = get_status_value(status_info, 'y1', 'user_setpoint', 'units')
        y_user = get_status_value(status_info, 'y1', 'position')
        y_dial = get_status_value(status_info, 'y1', 'dial_position', 'value')

        hn_units = get_status_value(status_info, 'h1n', 'user_setpoint',
                                    'units')
        hn_user = get_status_value(status_info, 'h1n', 'position')
        hn_dial = get_status_value(status_info, 'h1n', 'dial_position',
                                   'value')

        hp_units = get_status_value(status_info, 'h1p', 'user_setpoint',
                                    'units')
        hp_user = get_status_value(status_info, 'h1p', 'position')
        hp_dial = get_status_value(status_info, 'h1p', 'dial_position',
                                   'value')

        diode_units = get_status_value(status_info, 'diode2', 'user_setpoint',
                                       'units')
        diode_user = get_status_value(status_info, 'diode', 'position')
        diode_dial = get_status_value(status_info, 'diode', 'dial_position',
                                      'value')
        # tower 2
        z2_user = get_status_value(status_info, 'z2', 'position')
        z2_dial = get_status_value(status_info, 'z2', 'dial_position', 'value')

        x2_user = get_status_value(status_info, 'x2', 'position')
        x2_dial = get_status_value(status_info, 'x2', 'dial_position', 'value')

        th2_user = get_status_value(status_info, 'th2', 'position')
        th2_dial = get_status_value(status_info, 'th2', 'dial_position',
                                    'value')

        chi2_user = get_status_value(status_info, 'ch2', 'position')
        chi2_dial = get_status_value(status_info, 'ch2', 'dial_position',
                                     'value')

        y2_user = get_status_value(status_info, 'y2', 'position')
        y2_dial = get_status_value(status_info, 'y2', 'dial_position', 'value')

        hn2_user = get_status_value(status_info, 'h2n', 'position')
        hn2_dial = get_status_value(status_info, 'h2n', 'dial_position',
                                    'value')

        hp2_user = get_status_value(status_info, 'h2p', 'position')
        hp2_dial = get_status_value(status_info, 'h2p', 'dial_position',
                                    'value')

        diode2_user = get_status_value(status_info, 'diode2', 'position')
        diode2_dial = get_status_value(status_info, 'diode2', 'dial_position',
                                       'value')
        # diagnostics
        dh_units = get_status_value(status_info, 'dh', 'user_setpoint',
                                    'units')
        dh_user = get_status_value(status_info, 'dh', 'position')
        dh_dial = get_status_value(status_info, 'dh', 'dial_position', 'value')

        dv_units = get_status_value(status_info, 'dv', 'user_setpoint',
                                    'units')
        dv_user = get_status_value(status_info, 'dv', 'position')
        dv_dial = get_status_value(status_info, 'dv', 'dial_position', 'value')

        dr_units = get_status_value(status_info, 'dr', 'user_setpoint',
                                    'units')
        dr_user = get_status_value(status_info, 'dr', 'position')
        dr_dial = get_status_value(status_info, 'dr', 'dial_position', 'value')

        df_units = get_status_value(status_info, 'df', 'user_setpoint',
                                    'units')
        df_user = get_status_value(status_info, 'df', 'position')
        df_dial = get_status_value(status_info, 'df', 'dial_position', 'value')

        dd_units = get_status_value(status_info, 'dd', 'user_setpoint',
                                    'units')
        dd_user = get_status_value(status_info, 'dd', 'position')
        dd_dial = get_status_value(status_info, 'dd', 'dial_position', 'value')

        yag_zoom_units = get_status_value(status_info, 'yag_zoom',
                                          'user_setpoint', 'units')
        yag_zoom_user = get_status_value(status_info, 'yag_zoom', 'position')
        yag_zoom_dial = get_status_value(status_info, 'yag_zoom',
                                         'dial_position', 'value')

        def form(left_str, center_str, right_str):
            return f'{left_str:<15}{center_str:>25}{right_str:>25}'

        def ff(float_str):
            if isinstance(float_str, Number):
                return f'{float_str:.4f}'
            return float_str

        return f"""\
{hutch}LODCM Motor Status Positions
Current Configuration: {configuration} ({ref})
-----------------------------------------------------------------
{form(' ', 'Crystal Tower 1', 'Crystal Tower 2')}
{form(f'z [{z_units}]', f'{ff(z_user)} ({ff(z_dial)})',
      f'{ff(z2_user)} ({ff(z2_dial)})')}
{form(f'x [{x_units}]', f'{ff(x_user)} ({ff(x_dial)})',
      f'{ff(x2_user)} ({ff(x2_dial)})')}
{form(f'th [{th_units}]', f'{ff(th_user)} ({ff(th_dial)})',
      f'{ff(th2_user)} ({ff(th2_dial)})')}
{form(f'chi [{chi_units}]', f'{ff(chi_user)} ({ff(chi_dial)})',
      f'{ff(chi2_user)} ({ff(chi2_dial)})')}
{form(f'y [{y_units}]', f'{ff(y_user)} ({ff(y_dial)})',
      f'{ff(y2_user)} ({ff(y2_dial)})')}
{form(f'hn [{hn_units}]', f'{ff(hn_user)} ({ff(hn_dial)})',
      f'{ff(hn2_user)} ({ff(hn2_dial)})')}
{form(f'hp [{hp_units}]', f'{ff(hp_user)} ({ff(hp_dial)})',
      f'{ff(hp2_user)} ({ff(hp2_dial)})')}
{form(f'diode [{diode_units}]', f'{ff(diode_user)} ({ff(diode_dial)})',
      f'{ff(diode2_user)} ({ff(diode2_dial)})')}
-----------------------------------------------------------------
{form(' ', 'Diagnostic Tower', ' ')}
{form(f'diag r [{dr_units}]', f'{ff(dr_user)} ({ff(dr_dial)})', '')}
{form(f'diag h [{dh_units}]', f'{ff(dh_user)} ({ff(dh_dial)})', '')}
{form(f'diag v [{dv_units}]', f'{ff(dv_user)} ({ff(dv_dial)})', '')}
{form(f'filter [{df_units}]', f'{ff(df_user)} ({ff(df_dial)})', '')}
{form(f'diode [{dd_units}]', f'{ff(dd_user)} ({ff(dd_dial)})', '')}
{form(f'navitar [{yag_zoom_units}]',
      f'{ff(yag_zoom_user)} ({ff(yag_zoom_dial)})', '')}
"""


class SimLODCM(LODCM):
    """Test version of the LODCM object."""
    # tower 1
    x1 = Cpt(FastMotor, limits=(-100, 100))
    y1 = Cpt(FastMotor, limits=(-100, 100))
    z1 = Cpt(FastMotor, limits=(-100, 100))
    th1 = Cpt(FastMotor, limits=(-100, 100))
    ch1 = Cpt(FastMotor, limits=(-100, 100))
    h1n = Cpt(FastMotor, limits=(-100, 100))
    h1p = Cpt(FastMotor, limits=(-100, 100))
    # tower 2
    z2 = Cpt(FastMotor, limits=(-100, 100))
    x2 = Cpt(FastMotor, limits=(-100, 100))
    y2 = Cpt(FastMotor, limits=(-100, 100))
    th2 = Cpt(FastMotor, limits=(-100, 100))
    ch2 = Cpt(FastMotor, limits=(-100, 100))
    h2n = Cpt(FastMotor, limits=(-100, 100))
    diode2 = Cpt(FastMotor, limits=(-100, 100))
    # TOWER DIAG
    dh = Cpt(FastMotor, limits=(-100, 100))
    dv = Cpt(FastMotor, limits=(-100, 100))
    dr = Cpt(FastMotor, limits=(-100, 100))
    df = Cpt(FastMotor, limits=(-100, 100))
    dd = Cpt(FastMotor, limits=(-100, 100))
    yag_zoom = Cpt(FastMotor, limits=(-100, 100))
