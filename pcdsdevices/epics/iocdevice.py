#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define common features among LCLS devices. This includes things like the
iocAdmin module that all LCLS devices share but are not guaranteed outside of
LCLS.
"""
from .component import FormattedComponent
from .device import Device
from .iocadmin import IocAdmin


class IocDevice(Device):
    """
    Ophyd subclass for devices that represent LCLS-specific IOCs.
    """
    ioc = FormattedComponent(IocAdmin, "{self._iocadmin}")

    def __init__(self, prefix, *, ioc="", read_attrs=None, name=None,
                 **kwargs):
        self._iocadmin = ioc
        super().__init__(prefix, read_attrs=read_attrs, name=name, **kwargs)
