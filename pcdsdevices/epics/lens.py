"""
Basic Beryllium Lens XFLS
"""
############
# Standard #
############

###############
# Third Party #
###############
from ophyd import Component as C
from ophyd.status import wait as status_wait

##########
# Module #
##########
from .device import Device
from .signal import EpicsSignal
from .state  import SubscriptionStatus

class XFLS(Device):
    """
    XFLS Device

    The XFLS device has flexibility on what the state names are ultimately
    called, therefore this class simply interpets the base signal without
    providing the ability to check each individual state
    """
    state = C(EpicsSignal,'', write_pv=':GO')
    SUB_ST_CH = 'sub_state_changed'
    _default_sub = SUB_ST_CH

    @property
    def inserted(self):
        """
        Whether the lens is considered in
        """
        return self.state.value in list(range(1,4))

    @property
    def removed(self):
        """
        Whether the lens is removed
        """
        return self.state.value == 4

    def remove(self, wait=False, timeout=None, **kwargs):
        """
        Remove XFLS from the beamline

        Parameters
        ----------
        wait : bool

        timeout : float, optional
            Default timeout to wait mark the request as a failure

        Returns
        -------
        SubscriptionStatus:
            Future that reports the completion of the request
        """
        #Place command
        self.state.put(4)
        def cb():
            return self.state.value == 4
        status = SubscriptionStatus(self.state, cb, timeout=timeout)
        #Optional wait
        if wait:
            status_wait(status)
        return status

    def subscribe(self, cb, event_type=None, run=False):
        """
        Subscribe to changes in the XFLS state

        This simply maps to the :attr:`.state` component

        Parameters
        ----------
        cb : callable
            Callback to be run

        event_type : str, optional
            Type of event to run callback on

        run : bool, optional
            Run the callback immediatelly
        """
        return self.state.subscribe(cb, event_type=event_type, run=run)
