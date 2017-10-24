#!/usr/bin/env python
# -*- coding: utf-8 -*-
from threading import Event, Thread

from ophyd.status import MoveStatus, wait as status_wait

from ..interface import BranchingInterface
from .device import Device
from .state import statesrecord_class, InOutStates
from .component import Component


LodcmStates = statesrecord_class("LodcmStates", ":OUT", ":C", ":Si")
YagLomStates = statesrecord_class("YagLomStates", ":OUT", ":YAG", ":SLIT1",
                                  ":SLIT2", ":SLIT3")
DectrisStates = statesrecord_class("DectrisStates", ":OUT", ":DECTRIS",
                                   ":SLIT1", ":SLIT2", ":SLIT3", ":OUTLOW")
FoilStates = statesrecord_class("FoilStates", ":OUT", ":Mo", ":Zr", ":Zn",
                                ":Cu", ":Ni", ":Fe", "Ti")


class LODCM(Device, metaclass=BranchingInterface):
    """
    Large Offset Dual Crystal Monochromator

    This is the device that allows XPP and XCS to multiplex with downstream
    hutches. It contains two crystals that steer/split the beam and a number of
    diagnostic devices between them. Beam can continue onto the main line, onto
    the mono line, onto both, or onto neither.
    """
    h1n_state = Component(LodcmStates, ":H1N")
    h2n_state = Component(LodcmStates, ":H2N")
    yag_state = Component(YagLomStates, ":DV")
    dectris_state = Component(DectrisStates, ":DH")
    diode_state = Component(InOutStates, ":DIODE")
    foil_state = Component(FoilStates, ":FOIL")

    def __init__(self, prefix, *, name, main_line=None, mono_line='MONO',
                 **kwargs):
        self.main_line = main_line or self.db.beamline
        self.mono_line = mono_line
        super().__init__(prefix, name=name, **kwargs)

    @property
    def destination(self):
        """
        Return where the light is going at the current LODCM
        state.

        Returns
        -------
        destination: list of str
            self.main_line if the light continues on the main line.
            self.mono_line if the light continues on the mono line.
        """
        # H2N:     OUT      C       Si
        table = [["MAIN", "MAIN", "MAIN"],  # H1N at OUT
                 ["MAIN", "BOTH", "MAIN"],  # H1N at C
                 ["BLOCKED", "BLOCKED", "MONO"]]  # H1N at Si
        n1 = ("OUT", "C", "Si").index(self.h1n_state.value)
        n2 = ("OUT", "C", "Si").index(self.h2n_state.value)
        state = table[n1][n2]
        if state == "MAIN":
            return [self.main_line]
        elif state == "BLOCKED":
            return []
        else:
            if state == "MONO" and self.diag_clear:
                return [self.mono_line]
            if state == "BOTH":
                if self.diag_clear:
                    return [self.main_line, self.mono_line]
                else:
                    return [self.main_line]
        return []

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
    def diag_clear(self):
        """
        Returns
        -------
        diag_clear: bool
            False if the diagnostics will prevent beam.
        """
        yag_clear = self.yag_state.value == 'OUT'
        dectris_clear = self.dectris_state.value in ('OUT', 'OUTLOW')
        diode_clear = self.diode_state.value in ('IN', 'OUT')
        foil_clear = self.foil_state.value == 'OUT'
        return all((yag_clear, dectris_clear, diode_clear, foil_clear))

    @property
    def inserted(self):
        """
        Returns
        -------
        inserted: bool
            False if the diagnostics are in or if we have no destinations.
        """
        return not (self.destination and self.diag_clear)

    @property
    def removed(self):
        """
        Returns
        -------
        removed: bool
            True if diagnostics are clear or if the main line is a destination.
        """
        return self.diag_clear or self.main_line in self.destination

    def remove(self, wait=False, timeout=None, finished_cb=None, **kwargs):
        """
        Moves the diagnostics out of the beam.

        Parameters
        ----------
        wait: bool, optional
            If True, wait for motion to complete.

        timeout: float, optional
            If provided, mark the status as failed if the movement does not
            complete within this many seconds.

        finished_cb: func, optional
            Callback function to be run once the motion has completed.

        Returns
        -------
        status: ophyd.status.MoveStatus
            Status object that will be marked finished when all diagnostics are
            done moving and will time out after the given timeout.
        """
        if self.dectris_state.value == 'OUTLOW':
            dset = 'OUTLOW'
        else:
            dset = 'OUT'
        status = self.lodcm_move(yag='OUT', dectris=dset, diode='OUT',
                                 foil='OUT', timeout=timeout, **kwargs)
        if finished_cb is not None:
            status.finished_cb = finished_cb

        if wait:
            status_wait(status)

        return status

    def lodcm_move(self, h1n=None, h2n=None, yag=None, dectris=None,
                   diode=None, foil=None, timeout=None):
        """
        Move each component of the LODCM to the given state.

        Parameters
        ----------
        h1n: string, optional
            OUT, C, or Si

        h2n: string, optional
            OUT, C, or Si

        yag: string, optional
            OUT, YAG, SLIT1, SLIT2, or SLIT3

        dectris: string, optional
            OUT, DECTRIS, SLIT1, SLIT2, SLIT3, OUTLOW

        diode: string, optional
            OUT or IN

        foil: string, optional
            OUT, Mo, Zr, Zn, Cu, Ni, Fe, or Ti

        timeout: float, optional
            Mark status as failed after this many seconds.

        Returns
        -------
        status: MoveStatus
            Status object that will be marked as finished once all components
            are done moving.
        """
        states = (h1n, h2n, yag, dectris, diode, foil)
        obj = (self.h1n_state, self.h2n_state, self.yag_state,
               self.dectris_state, self.diode_state, self.foil_state)
        done_statuses = []
        for state, obj in zip(states, obj):
            if state is not None:
                status = obj.move(state)
                done_statuses.append(status)

        lodcm_status = MoveStatus(self, timeout=timeout)
        if not done_statuses:
            lodcm_status._finished(success=True)
            return lodcm_status

        events = []
        for i, status in enumerate(done_statuses):
            event = Event()
            events.append(event)
            status.finished_cb = self._make_mark_event(event)

        finisher = Thread(target=self._status_finisher,
                          args=(events, lodcm_status))
        finisher.start()
        return lodcm_status

    def _make_mark_event(self, event):
        """
        Create callback for combining statuses
        """
        def mark_event(*args, **kwargs):
            event.set()
        return mark_event

    def _status_finisher(self, events, status, timeout=None):
        """
        Mark status as finished or short-circuit on timeout
        """
        for ev in events:
            ok = ev.wait(timeout=timeout)
            if not ok:
                return
        status._finished(success=True)
