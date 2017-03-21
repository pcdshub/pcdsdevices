#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module to define the PulsePicker device subclass.
"""
from ophyd import Component, EpicsSignalRO
from .lclsdevice import LCLSDevice
from .state import InOutStates, InOutCCMStates


class PulsePicker(LCLSDevice):
    """
    Device that lets us pick which beam pulses reach the sample.
    """
    position = Component(InOutStates)
    mode = Component(EpicsSignalRO, ":SE")

    def __init__(self, prefix, *, in_out_prefix=None, ioc="",
                 read_attrs=None, name=None, **kwargs):
        super().__init__(self, prefix, **kwargs)


class PulsePickerCCM(PulsePicker):
    """
    Device that lets us pick which beam pulses reach the sample.
    This is the version with a third position state in addition to IN and OUT,
    and that's the CCM state: IN but at the CCM offset.
    """
    position = Component(InOutCCMStates)
