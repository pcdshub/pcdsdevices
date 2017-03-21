#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to define the PulsePicker device subclass.
"""
from ophyd import Component, FormattedComponent, EpicsSignalRO
from .lclsdevice import LCLSDevice
from .state import InOutStates, InOutCCMStates


class PulsePicker(LCLSDevice):
    """
    Device that lets us pick which beam pulses reach the sample.
    """
    position = FormattedComponent(InOutStates, "{self._in_out}")
    mode = Component(EpicsSignalRO, ":SE")

    def __init__(self, prefix, *, in_out_prefix="", ioc="",
                 read_attrs=None, name=None, **kwargs):
        self._in_out = in_out_prefix
        append_kwargs = dict(ioc=ioc, read_attrs=read_attrs, name=name)
        kwargs.update(append_kwargs)
        super().__init__(self, prefix, **kwargs)


class PulsePickerCCM(PulsePicker):
    """
    Device that lets us pick which beam pulses reach the sample.
    This is the version with a third position state in addition to IN and OUT,
    and that's the CCM state: IN but at the CCM offset.
    """
    position = Component(InOutCCMStates)
