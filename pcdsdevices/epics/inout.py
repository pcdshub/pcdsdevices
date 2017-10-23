#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .device import Device
from .component import Component as Cmp
from .state import InOutStates, statesrecord_class


class InOutDevice(Device):
    """
    Device that has two states, IN and OUT, that blocks the beam while IN.
    """
    state = Cmp(InOutStates, '')

    @property
    def inserted(self):
        return self.state.value == 'IN'

    @property
    def removed(self):
        return self.state.value == 'OUT'

    def remove(self, wait=False, timeout=None, finished_cb=None, **kwargs):
        return self.state.move('OUT', moved_cb=finished_cb, timeout=timeout,
                               wait=wait, **kwargs)

    def subscribe(self, cb, event_type=None, run=False, **kwargs):
        self.state.subscribe(cb, event_type=event_type, run=run, **kwargs)


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
    state = Cmp(TTStates, '')

    @property
    def inserted(self):
        return self.state.value in ('TT', 'REFL')
