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
    SUB_STATE = 'sub_state_changed'
    _default_sub = SUB_STATE

    def __init__(self, prefix, *, name=None, parent=None,
                 read_attrs=None, **kwargs):
        if read_attrs is None:
            read_attrs = ["state"]

        super().__init__(prefix, name=name, parent=parent,
                         read_attrs=read_attrs, **kwargs)
        #Subscribe to state changes
        self.state.subscribe(self._on_state_change,
                             run=False)
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

    def _on_state_change(self,  **kwargs):
        """
        Performed on a state change
        """
        #Avoid duplicate keywords
        kwargs.pop('sub_type', None)
        #Run subscriptions
        self._run_subs(sub_type=self.SUB_STATE, **kwargs)
