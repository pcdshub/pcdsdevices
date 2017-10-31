#!/usr/bin/env python
# -*- coding: utf-8 -*-
from copy import deepcopy
from .signal import EpicsSignal, EpicsSignalRO
from .component import Component, FormattedComponent
from .device import Device
from .state import InOutStates, InOutCCMStates, statesrecord_class
from .state import SubscriptionStatus


class PickerBlade(Device):
    """
    Represent the pulse picker blade as separte device
    """
    simple_state = Component(EpicsSignalRO, ":DF")
    force_close  = Component(EpicsSignal,   ":S_CLOSE")
    #Subscription information
    SUB_STATE = 'sub_state_changed'
    _default_sub = SUB_STATE

    def __init__(self, prefix, *, name=None, read_attrs=None, **kwargs):
        self._has_subscribed = False
        #Instantiate ophyd level
        if read_attrs is None:
            read_attrs = ['simple_state']
        super().__init__(prefix, name=name, read_attrs=read_attrs, **kwargs)

    @property
    def inserted(self):
        """
        Whether the blade is open
        """
        return self.simple_state.value == 1

    @property
    def removed(self):
        """
        Whether the blade is closed
        """
        return self.simple_state.value == 0

    def remove(self, wait=False, timeout=None):
        """
        Remove the PulsePicker
        """
        #Order move
        self.force_close.put(1)
        #Create status
        status = SubscriptionStatus(self,
                                    lambda *args, **kwargs: self.removed,
                                    event_type = self.SUB_STATE,
                                    timeout=timeout)
        #Optionally wait for status
        if wait:
            status_wait(status)

        return status
    
    def subscribe(self, cb, event_type=None, run=True):
        """
        Subscribe to changes of the valve

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
            #Subscribe to state changes
            self.simple_state.subscribe(self._blade_moved, run=False)
            self._has_subscribed = True
        super().subscribe(cb, event_type=event_type, run=run)

    def _blade_moved(self, **kwargs):
        """
        Blade has moved
        """
        kwargs.pop('sub_type', None)
        kwargs.pop('obj', None)
        self._run_subs(sub_type=self.SUB_STATE, obj=self, **kwargs)


class PulsePicker(Device):
    """
    Device that lets us pick which beam pulses reach the sample.
    """
    in_out = FormattedComponent(InOutStates, "{self._states}")
    mode = Component(EpicsSignalRO, ":SE", string=True)
    #Blade subdevice
    blade = FormattedComponent(PickerBlade, "{self.prefix}")

    def __init__(self, prefix, *, states="",
                 read_attrs=None, name=None, **kwargs):
        self._states = states
        if read_attrs is None:
            read_attrs = ["mode", "blade", "in_out"]
        super().__init__(prefix, read_attrs=read_attrs, name=name,
                         **kwargs)

    def move_out(self):
        """
        Move the pulsepicker to the "out" position in y.
        """
        self.in_out.value = "OUT"

    def move_in(self):
        """
        Move the pulsepicker to the "in" position in y.
        """
        self.in_out.value = "IN"


class PulsePickerCCM(PulsePicker):
    """
    Device that lets us pick which beam pulses reach the sample.
    This is the version with a third position state in addition to IN and OUT,
    and that's the CCM state: IN but at the CCM offset.
    """
    in_out = deepcopy(PulsePicker.in_out)
    in_out.cls = InOutCCMStates

    def move_ccm(self):
        """
        Move the pulsepicker to the "ccm" position in y.
        """
        self.in_out.value = "CCM"


TempStates = statesrecord_class("TempStates", ":PINK", ":CCM", ":OUT")


class PulsePickerPink(PulsePickerCCM):
    """
    Current state syntax that I plan to change
    """
    in_out = deepcopy(PulsePickerCCM.in_out)
    in_out.cls = TempStates

    def move_in(self):
        self.in_out.value = "PINK"
