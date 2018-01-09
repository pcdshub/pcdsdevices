#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ophyd import Device, Component as C

from ..state import InOutStates, statesrecord_class


class InOutDevice(Device):
    """
    Device that has two states, IN and OUT, that blocks the beam while IN.
    """
    state = C(InOutStates, '')
    #Subscription types
    SUB_STATE = 'sub_state_changed'
    _default_sub = SUB_STATE

    def __init__(self, *args, **kwargs):
        self._has_subscribed = False
        super().__init__(*args, **kwargs)

    @property
    def inserted(self):
        return self.state.value == 'IN'

    @property
    def removed(self):
        return self.state.value == 'OUT'

    def remove(self, wait=False, timeout=None, finished_cb=None, **kwargs):
        return self.state.move('OUT', moved_cb=finished_cb, timeout=timeout,
                               wait=wait, **kwargs)

    def subscribe(self, cb, event_type=None, run=False):
        """
        Subscribe to changes of the InOutDevice

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
            self.state.subscribe(self._on_state_change, run=False)
            self._has_subscribed = True
        super().subscribe(cb, event_type=event_type, run=run)

    def _on_state_change(self, **kwargs):
        """
        Callback run on state change
        """
        kwargs.pop('sub_type', None)
        kwargs.pop('obj', None)
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)

class Reflaser(InOutDevice):
    """
    Mirror that is inserted into the beam to point a reference laser along the
    beam path.
    """
    pass


class TTReflaser(Reflaser):
    """
    Motor stack that includes both a timetool and a reflaser.
    """
    TTStates = statesrecord_class('TTStates', ':TT', ':REFL', ':OUT')
    state = C(TTStates, '')

    @property
    def inserted(self):
        return self.state.value in ('TT', 'REFL')
