#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oh the hue manatee
"""

from ophyd.signal import EpicsSignalBase, EpicsSignal, EpicsSignalRO

class LCLSEpicsSignalBase(EpicsSignalBase):
#    def __init__(self, read_pv, *,
#                 pv_kw=None,
#                 string=False,
#                 auto_monitor=False,
#                 name=None,
#                 **kwargs):
#        base_pv_kw = dict(connection_timeout=1.0)
#        if isinstance(pv_kw, dict):
#            base_pv_kw.update(pv_kw)
#        pv_kw = base_pv_kw
#        super().__init__(read_pv, pv_kw=pv_kw, string=string,
#                         auto_monitor=auto_monitor, name=name, **kwargs)
    pass


class LCLSEpicsSignal(EpicsSignal, LCLSEpicsSignalBase):
    pass


class LCLSEpicsSignalRO(EpicsSignalRO, LCLSEpicsSignalBase):
    pass
