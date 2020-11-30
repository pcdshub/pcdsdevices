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
from ophyd.status import wait as status_wait

from .component import UnrelatedComponent as UCpt
from .doc_stubs import insert_remove
from .inout import InOutRecordPositioner
from .interface import BaseInterface
from .epics_motor import IMS, PCDSMotorBase, Motor
from .sim import FastMotor
from types import SimpleNamespace

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


class LOMXtalChi1(InOutRecordPositioner):
    states_list = ['C', 'Si']


class LOMXtalChi2(InOutRecordPositioner):
    states_list = ['C', 'Si']


class H2N(InOutRecordPositioner):
    states_list = ['C', 'Si']


class Y1(InOutRecordPositioner):
    states_list = ['C', 'Si']


class Y2(InOutRecordPositioner):
    states_list = ['C', 'Si']


# chi1 = ['C', 'Si']
# chi2 = ['C', 'Si']
# dh = ['DECTRIS', 'OUT', 'OUTLOW', 'SLIT1', 'SLIT2', 'SLIT3']
# dv = ['OUT', 'SLIT1', 'SLIT2', 'SLIT3', 'YAG']
# diode = ['OUT', 'IN']
# h1n = ['C', 'OUT', 'Si']
# h2n = ['C', 'Si']
# y1 = ['C', 'Si']
# y2 = ['C', 'Si']


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
        LOM Xtal1 Z

    x1_prefix : str
        LOM Xtal1 X

    y1_prefix : str
        LOM Xtal1 Y

    th1_prefix : str
        LOM Xtal1 Theta

    ch1_prefix : str
        LOM Xtal1 Chi

    h1n_prefix : str
        LOM Xtal1 Hn

    h1p_prefix : str
        LOM Xtal1 Hp

    th1f_prefix : str

    ch1f_prefix : str

    z2_prefix : str
        LOM Xtal2 Z

    x2_prefix : str
        LOM Xtal2 X

    y2_prefix : str
        LOM Xtal2 Y

    th2_prefix : str
        LOM Xtal2 Theta

    ch2_prefix : str
        LOM Xtal2 Chi

    h2n_prefix : str
        LOM Xtal2 Hn

    diode2_orefix : str
        LOM Xtal2 PIPS

    th2f_prefix : str

    ch2f_prefix : str
    """
    h1n = Cpt(H1N, ':H1N', kind='hinted')
    yag = Cpt(YagLom, ":DV", kind='omitted')
    dectris = Cpt(Dectris, ":DH", kind='omitted')
    diode = Cpt(Diode, ":DIODE", kind='omitted')
    foil = Cpt(Foil, ":FOIL", kind='omitted')

    # Crystal Tower 1
    # z1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 Z')
    # x1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 X')
    # y1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 Y')
    # th1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 Theta')
    # ch1 = UCpt(IMS, kind='normal', doc='LOM Xtal1 Chi')
    # h1n = UCpt(IMS, kind='normal', doc='LOM Xtal1 Hn')
    # h1p = UCpt(IMS, kind='normal', doc='LOM Xtal1 Hp')
    # th1f = UCpt(PCDSMotorBase, kind='normal', doc='')
    # ch1f = UCpt(PCDSMotorBase, kind='normal', doc='')
    # # Crystal Tower 2
    # z2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 Z')
    # x2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 X')
    # y2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 Y')
    # th2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 Theta')
    # ch2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 Chi')
    # h2n = UCpt(IMS, kind='normal', doc='LOM Xtal2 Hn')
    # diode2 = UCpt(IMS, kind='normal', doc='LOM Xtal2 PIPS')
    # th2f = UCpt(PCDSMotorBase, kind='normal', doc='')
    # ch2f = UCpt(PCDSMotorBase, kind='normal', doc='')
    # # Diagnostic Tower
    # dh = UCpt(IMS, kind='normal', doc='LOM Dia H')
    # dv = UCpt(IMS, kind='normal', doc='LOM Dia V')
    # dr = UCpt(IMS, kind='normal', doc='LOM Dia Theta')
    # df = UCpt(IMS, kind='normal', doc='LOM Dia Filter Wheel')
    # dd = UCpt(IMS, kind='normal', doc='LOM Dia PIPS')
    # yag_zoom = UCpt(IMS, kind='normal', doc='LOM Zoom')

    # QIcon for UX
    _icon = 'fa.share-alt-square'

    tab_whitelist = ['h1n', 'yag', 'dectris', 'diode', 'foil', 'remove_dia']

    def __init__(self, prefix, *, name, main_line='MAIN', mono_line='MONO',
                 **kwargs):
        #  UCpt.collect_prefixes(self, kwargs)
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

    remove_dia.__doc__ += insert_remove


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
    'h1n': {'prefix': 'XPP:MON:MMS:09', 'description': 'LOM Xtal1 Hn',
            'motor': Motor('XPP:MON:MMS:09', name='h1n')},
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


class LODCMWithDefaults(LODCM):
    # Crystal Tower 1
    z1 = LODCM_MOTORS['z1']['motor']
    x1 = LODCM_MOTORS['x1']['motor']
    y1 = LODCM_MOTORS['y1']['motor']
    th1 = LODCM_MOTORS['th1']['motor']
    ch1 = LODCM_MOTORS['ch1']['motor']
    h1n = LODCM_MOTORS['h1n']['motor']
    h1p = LODCM_MOTORS['h1p']['motor']
    th1f = LODCM_MOTORS['th1f']['motor']
    ch1f = LODCM_MOTORS['ch1f']['motor']
    # Crystal Tower 2
    z2 = LODCM_MOTORS['z2']['motor']
    x2 = LODCM_MOTORS['x2']['motor']
    y2 = LODCM_MOTORS['y2']['motor']
    th2 = LODCM_MOTORS['th2']['motor']
    ch2 = LODCM_MOTORS['ch2']['motor']
    h2n = LODCM_MOTORS['h2n']['motor']
    diode2 = LODCM_MOTORS['diode2']['motor']
    th2f = LODCM_MOTORS['th2f']['motor']
    ch2f = LODCM_MOTORS['ch2f']['motor']
    # Diagnostic Tower
    dh = LODCM_MOTORS['dh']['motor']
    dv = LODCM_MOTORS['dv']['motor']
    dr = LODCM_MOTORS['dr']['motor']
    df = LODCM_MOTORS['df']['motor']
    dd = LODCM_MOTORS['dd']['motor']
    yag_zoom = LODCM_MOTORS['yag_zoom']['motor']


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
    th1f = Cpt(FastMotor, limits=(-100, 100))
    ch1f = Cpt(FastMotor, limits=(-100, 100))
    # tower 2
    z2 = Cpt(FastMotor, limits=(-100, 100))
    x2 = Cpt(FastMotor, limits=(-100, 100))
    y2 = Cpt(FastMotor, limits=(-100, 100))
    th2 = Cpt(FastMotor, limits=(-100, 100))
    ch2 = Cpt(FastMotor, limits=(-100, 100))
    h2n = Cpt(FastMotor, limits=(-100, 100))
    diode2 = Cpt(FastMotor, limits=(-100, 100))
    th2f = Cpt(FastMotor, limits=(-100, 100))
    ch2f = Cpt(FastMotor, limits=(-100, 100))
    # TOWER DIAG
    dh = Cpt(FastMotor, limits=(-100, 100))
    dv = Cpt(FastMotor, limits=(-100, 100))
    dr = Cpt(FastMotor, limits=(-100, 100))
    df = Cpt(FastMotor, limits=(-100, 100))
    dd = Cpt(FastMotor, limits=(-100, 100))
    yag_zoom = Cpt(FastMotor, limits=(-100, 100))
