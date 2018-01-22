from threading import RLock

from ophyd import Device, Component
from ophyd.status import DeviceStatus, wait as status_wait

from ..inout import InOutRecordPositioner


class H1NStates(InOutRecordPositioner):
    states_list = ['OUT', 'C', 'Si']
    in_states = ['C', 'Si']


class YagLomStates(InOutRecordPositioner):
    states_list = ['OUT', 'YAG', 'SLIT1', 'SLIT2', 'SLIT3']
    in_states = ['YAG', 'SLIT1', 'SLIT2', 'SLIT3']


class DectrisStates(InOutRecordPositioner):
    states_list = ['OUT', 'DECTRIS', 'SLIT1', 'SLIT2', 'SLIT3', 'OUTLOW']
    in_states = ['DECTRIS', 'SLIT1', 'SLIT2', 'SLIT3']
    out_states = ['OUT', 'OUTLOW']


class FoilStates(InOutRecordPositioner):
    states_list = ['OUT']
    in_states = []
    # This class needs rethinking because the foils are different between the
    # two lodcm instances


class LODCM(Device):
    """
    Large Offset Dual Crystal Monochromator

    This is the device that allows XPP and XCS to multiplex with downstream
    hutches. It contains two crystals that steer/split the beam and a number of
    diagnostic devices between them. Beam can continue onto the main line, onto
    the mono line, onto both, or onto neither.
    """
    h1n = Component(H1NStates, ":H1N")
    yag = Component(YagLomStates, ":DV")
    dectris = Component(DectrisStates, ":DH")
    diode = Component(InOutRecordPositioner, ":DIODE")
    foil = Component(FoilStates, ":FOIL")

    SUB_STATE = 'sub_state_changed'
    _default_sub = SUB_STATE

    def __init__(self, prefix, *, name, main_line=None, mono_line='MONO',
                 **kwargs):
        super().__init__(prefix, name=name, **kwargs)
        if main_line is None:
            try:
                main_line = self.db.beamline
            except AttributeError:
                main_line = 'MAIN'
        self.main_line = main_line
        self.mono_line = mono_line
        self._update_dest_lock = RLock()
        self._has_subscribed = False
        self._last_dest = None

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
        table = ["MAIN", "BOTH", "MONO", "BLOCKED"]
        states = ("OUT", "C", "Si", "Unknown")
        n1 = states.index(self.h1n.position)
        state = table[n1]
        if state == "MAIN":
            return [self.main_line]
        elif state == "BLOCKED":
            return []
        else:
            if state == "MONO":
                if self.diag_clear:
                    return [self.mono_line]
                else:
                    return []
            if state == "BOTH":
                if self.diag_clear:
                    return [self.main_line, self.mono_line]
                else:
                    return [self.main_line]
        return []

    def subscribe(self, cb, event_type=None, run=True):
        """
        Subscribe to changes in the LODCM destination

        Parameters
        ----------
        cb : callable
            Callback to be run

        event_type : str, optional
            Type of event to run callback on

        run : bool, optional
            Run the callback immediatelly
        """
        if not self._has_subscribed:
            self.h1n.subscribe(self._subs_update_destination, run=False)
            self.yag.subscribe(self._subs_update_destination, run=False)
            self.dectris.subscribe(self._subs_update_destination, run=False)
            self.diode.subscribe(self._subs_update_destination, run=False)
            self.foil.subscribe(self._subs_update_destination, run=False)
            self._has_subscribed = True
        super().subscribe(cb, event_type=event_type, run=run)

    def _subs_update_destination(self, *args, **kwargs):
        """
        To be run whenever any of the component states changes.
        If the destination has changed, run all SUB_STATE subs.
        """
        new_dest = self.destination
        with self._update_dest_lock:
            if new_dest != self._last_dest:
                self._last_dest = new_dest
                self._run_subs(sub_type=self.SUB_STATE)

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
        yag_clear = self.yag.position == 'OUT'
        dectris_clear = self.dectris.position in ('OUT', 'OUTLOW')
        diode_clear = self.diode.position in ('IN', 'OUT')
        foil_clear = self.foil.position == 'OUT'
        return all((yag_clear, dectris_clear, diode_clear, foil_clear))

    @property
    def inserted(self):
        """
        Returns
        -------
        inserted: bool
            True if h1n is in
        """
        return not self.removed

    @property
    def removed(self):
        """
        Returns
        -------
        removed: bool
            True if h1n is out
        """
        return self.h1n.position == "OUT"

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
        status: ophyd.status.DeviceStatus
            Status object that will be marked finished when all diagnostics are
            done moving and will time out after the given timeout.
        """
        if self.dectris.position == 'OUTLOW':
            dset = 'OUTLOW'
        else:
            dset = 'OUT'
        status = self.lodcm_move(yag='OUT', dectris=dset, diode='OUT',
                                 foil='OUT', timeout=timeout, **kwargs)
        if finished_cb is not None:
            status.add_callback(finished_cb)

        if wait:
            status_wait(status)

        return status

    def lodcm_move(self, h1n=None, yag=None, dectris=None,
                   diode=None, foil=None, timeout=None):
        """
        Move each component of the LODCM to the given state.

        Parameters
        ----------
        h1n: string, optional
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
        status: DeviceStatus
            Status object that will be marked as finished once all components
            are done moving.
        """
        states = (h1n, yag, dectris, diode, foil)
        obj = (self.h1n, self.yag, self.dectris, self.diode, self.foil)
        done_statuses = []
        for state, obj in zip(states, obj):
            if state is not None:
                status = obj.set(state)
                done_statuses.append(status)

        lodcm_status = DeviceStatus(self, timeout=timeout)
        if not done_statuses:
            lodcm_status._finished(success=True)
            return lodcm_status

        first_status = done_statuses[0]
        rest_status = done_statuses[1:]

        and_status = first_status
        for stat in rest_status:
            and_status = and_status & stat

        return and_status
