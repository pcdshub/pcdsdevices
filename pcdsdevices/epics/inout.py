#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .device import Device
from .component import Component as Cmp
from .state import InOutStates, statesrecord_class

class Reflaser(Device):
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


TTStates = statesrecord_class('TTStates', ':TT', ':REFL', ':OUT')

class TTReflaser(Reflaser):
    state = Cmp(TTStates, '')

    @property
    def inserted(self):
        return self.state.value in ('TT', 'REFL')
