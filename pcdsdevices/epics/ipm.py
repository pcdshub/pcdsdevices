#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .device import Device
from .state import statesrecord_class, InOutStates
from .component import Component, FormattedComponent
from .signal import EpicsSignalRO
from ophyd.status import wait as status_wait


TargetStates = statesrecord_class("TargetStates", ":OUT", ":TARGET1",
                                  ":TARGET2", ":TARGET3", ":TARGET4")


class IPM(Device):
    """
    Standard intensity position monitor. Consists of two stages, one for the
    diode and one for the target. This creates a scalar readback that is also
    available over EPICS.
    """
    diode = Component(InOutStates,   ":DIODE")
    target = Component(TargetStates, ":TARGET")
    data = FormattedComponent(EpicsSignalRO, "{self._data}")

    #Default subscriptions
    SUB_ST_CHG   = 'target_state_changed'
    _default_sub = SUB_ST_CHG
    transmission = 0.8 #Completely making up this number :)

    def __init__(self, prefix, *, data="", ioc="", name=None, parent=None,
                 read_attrs=None, **kwargs):
        #Default read attributes
        self._data = data
        if read_attrs is None:
            read_attrs = ["data"]

        super().__init__(prefix, ioc=ioc, name=name, parent=parent,
                         read_attrs=read_attrs, **kwargs)
        #Subscribe to state changes
        self.target.subscribe(self._target_moved,
                              event_type=self.target.SUB_RBK_CHG,
                              run=False)


    def target_in(self, target):
        """
        Move the target to one of the target positions

        Parameters
        ----------
        target, int
            Number of which target to move in. Must be one of 1, 2, 3, 4.
        """
        target = int(target)
        if 1 <= target <= 4:
            self.target.value = "TARGET{}".format(target)


    @property
    def inserted(self):
        """
        Report if the IPIMB is not OUT"
        """
        return self.target.value != "OUT"



    @property
    def removed(self):
        """
        Report if the IPM is inserted
        """
        return self.target.value == "OUT"



    def remove(self, *args, wait=False, **kwargs):
        """
        Remove the IPM by going to the `OUT` position

        Parameters
        ----------
        wait : bool, optional
            Wait for the status object to complete the move before returning

        timeout : float, optional
            Maximum time to wait for the motion. If None, the default timeout
            for this positioner is used

        settle_time: float, optional
            Delay after the set() has completed to indicate completion to the
            caller

        Returns
        -------
        status : MoveStatus
            Status object of the move

        Notes
        -----
        Instantiated for `lightpath` compatability
        """
        #Set to out
        status = self.target.state.set("OUT", **kwargs)
        #Wait on status
        if wait:
            status_wait(status)
        return status


    def diode_in(self):
        """
        Move the diode to the in position.
        """
        self.diode.value = "IN"


    def diode_out(self):
        """
        Move the diode to the out position.
        """
        self.diode.value = "OUT"


    def _target_moved(self, **kwargs):
        """
        Callback when device state has moved
        """
        #Avoid duplicate keywords
        kwargs.pop('sub_type', None)
        #Run subscriptions
        self._run_subs(sub_type=self.SUB_ST_CHG, **kwargs)
