"""
LODCM: Large offset dual-crystal monochrometer.

The scope of this module is to identify where the beam is intended to go after
passing through H1N, to manipulate the diagnostics, and to remove H1N for the
downstream hutches.

It will not be possible to align the device with the class, and there will be
no readback into the device's alignment. This is intended for a future update.
"""
import functools

from ophyd import Component as Cmp
from ophyd.signal import EpicsSignal
from ophyd.sim import NullStatus
from ophyd.status import wait as status_wait

from .inout import InOutRecordPositioner


class YagLom(InOutRecordPositioner):
    states_list = ['OUT', 'YAG', 'SLIT1', 'SLIT2', 'SLIT3']
    in_states = ['YAG', 'SLIT1', 'SLIT2', 'SLIT3']


class Dectris(InOutRecordPositioner):
    states_list = ['OUT', 'DECTRIS', 'SLIT1', 'SLIT2', 'SLIT3', 'OUTLOW']
    in_states = ['DECTRIS', 'SLIT1', 'SLIT2', 'SLIT3']
    out_states = ['OUT', 'OUTLOW']


class Foil(InOutRecordPositioner):
    states_list = ['OUT']
    in_states = []


class FoilXPP(Foil):
    states_list = ['OUT', 'Zr', 'Zn', 'Cu', 'Ni', 'Fe', 'Ti']
    in_states = ['Mo', 'Zr', 'Zn', 'Cu', 'Ni', 'Fe', 'Ti']


class FoilXCS(Foil):
    states_list = ['OUT', 'Mo', 'Zr', 'Ge', 'Cu', 'Ni', 'Fe', 'Ti']
    in_states = ['Mo', 'Zr', 'Ge', 'Cu', 'Ni', 'Fe', 'Ti']


class LODCM(InOutRecordPositioner):
    """
    Large Offset Dual Crystal Monochromator

    This is the device that allows XPP and XCS to multiplex with downstream
    hutches. It contains two crystals that steer/split the beam and a number of
    diagnostic devices between them. Beam can continue onto the main line, onto
    the mono line, onto both, or onto neither.

    This positioner only considers the h1n and diagnostic motors.
    """
    state = Cmp(EpicsSignal, ':H1N', write_pv=':H1N:GO')

    yag = Cmp(YagLom, ":DV")
    dectris = Cmp(Dectris, ":DH")
    diode = Cmp(InOutRecordPositioner, ":DIODE")
    foil = Cmp(Foil, ":FOIL")

    states_list = ['OUT', 'C', 'Si']
    in_states = ['C', 'Si']

    # TBH these are guessed. Please replace if you know better. These don't
    # need to be 100% accurate, but they should reflect a reasonable reduction
    # in transmission.
    _transmission = {'C': 0.8, 'Si': 0.7}

    def __init__(self, prefix, *, name, main_line='MAIN', mono_line='MONO',
                 **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        self.main_line = main_line
        self.mono_line = mono_line

    @property
    def branches(self):
        """
        Returns
        -------
        branches: list of str
            A list of possible destinations.
        """
        return [self.main_line, self.mono_line]

    @property
    def destination(self):
        """
        Return where the light is going at the current LODCM
        state. Indeterminate states will show as blocked.

        Returns
        -------
        destination: list of str
            self.main_line if the light continues on the main line.
            self.mono_line if the light continues on the mono line.
        """
        if self.position == 'OUT':
            dest = [self.main_line]
        elif self.position == 'Si':
            dest = [self.mono_line]
        elif self.position == 'C':
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
        diag_clear: bool
            False if the diagnostics will prevent beam.
        """
        yag_clear = self.yag.removed
        dectris_clear = self.dectris.removed
        foil_clear = self.foil.removed
        return all((yag_clear, dectris_clear, foil_clear))

    def remove_dia(self, moved_cb=None, timeout=None, wait=False):
        """
        Remove all diagnostic components.
        """
        status = NullStatus()
        for dia in (self.yag, self.dectris, self.diode, self.foil):
            status = status & dia.remove(timeout=timeout, wait=False)

        if moved_cb is not None:
            status.add_callback(functools.partial(moved_cb, obj=self))

        if wait:
            status_wait(status)

        return status


class LODCMXPP(LODCM):
    foil = Cmp(FoilXPP, ":FOIL")


class LODCMXCS(LODCM):
    foil = Cmp(FoilXCS, ":FOIL")
