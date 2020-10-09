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

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.sim import NullStatus
from ophyd.status import wait as status_wait

from .doc_stubs import insert_remove
from .inout import InOutRecordPositioner
from .interface import BaseInterface

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
    """

    h1n = Cpt(H1N, ':H1N', kind='hinted')
    yag = Cpt(YagLom, ":DV", kind='omitted')
    dectris = Cpt(Dectris, ":DH", kind='omitted')
    diode = Cpt(Diode, ":DIODE", kind='omitted')
    foil = Cpt(Foil, ":FOIL", kind='omitted')

    # QIcon for UX
    _icon = 'fa.share-alt-square'

    tab_whitelist = ['h1n', 'yag', 'dectris', 'diode', 'foil', 'remove_dia']

    def __init__(self, prefix, *, name, main_line='MAIN', mono_line='MONO',
                 **kwargs):
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
