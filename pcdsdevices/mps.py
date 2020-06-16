"""
Module for devices that are integrated with the MPS system.

These communicate with ACR via a single bit summary.
The results of these are published over EPICS and
interpreted by :class:`.MPS`.
"""
import logging

from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import FormattedComponent as FCpt

from .interface import BaseInterface

logger = logging.getLogger(__name__)


class MPSBase(BaseInterface):
    """
    Base MPS class.

    Used for shared methods between the individual `MPS` bit class and
    the `MPSLimits` class. The class handles much of the bookkeeping
    for both of these classes.

    Each subclass must reimplement:

    - :meth:`faulted`
    - :meth:`bypassed`
    - :meth:`_sub_to_children`
    """

    # Subscription information
    SUB_FAULT_CH = 'sub_mps_faulted'
    _default_sub = SUB_FAULT_CH
    tab_whitelist = ['tripped']

    def __init__(self, *args, veto=False, **kwargs):
        self.veto_capable = veto
        self._has_subscribed_fault = False
        super().__init__(*args, **kwargs)

    @property
    def tripped(self):
        """
        Whether this will trip the MPS system.

        This is based off of both the faulted state as well as any temporary
        bypasses on the MPS bit.
        """

        return self.faulted and not self.bypassed

    def subscribe(self, cb, event_type=None, run=True):
        """
        Subscribe to changes in the MPS.

        If this is the first subscription to the `SUB_FAULT_CH`, subscribe to
        any changes in the bypass or fault signals.
        """

        cid = super().subscribe(cb, event_type=event_type, run=run)
        # Subscribe child signals
        if event_type is None:
            event_type = self._default_sub
        if event_type == self.SUB_FAULT_CH and not self._has_subscribed_fault:
            self._sub_to_children()
            self._has_subscribed_fault = True
        return cid

    def _fault_change(self, *args, **kwargs):
        """Callback when the state of the MPS bit has changed."""
        kwargs.pop('sub_type', None)
        self._run_subs(sub_type=self.SUB_FAULT_CH, **kwargs)


class MPS(MPSBase, Device):
    """
    Class to interpret a single bit of MPS information.

    There are three major attributes of each MPS bit that are relevant to
    operations; :attr:`.faulted` , :attr:`.bypassed` and :attr:`.veto_capable`.
    The first is the most obvious: when the device is faulted, it reports as
    such to the MPS system. However, how this is actually interpreted by the
    MPS is determined by whether the bit is bypassed, and if there is a
    ``veto`` device upstream such that the fault can be safely ignored. The
    summary of both the `bypass` and `fault` signals is contained within
    :attr:`.tripped`.  The bypassed state is reported through EPICS as well but
    unfortunately whether a device is considered capable of  "veto-ing" or is
    vetoed by another device is not broadcast by EPICS so this is held within
    this device and the ``lightpath`` module.

    Parameters
    ----------
    prefix : str
        PV prefix of MPS information.

    name : str
        Name of MPS bit.

    veto : bool, optional
        Whether or not the the device is capable of vetoing downstream faults.
    """

    # Signals
    fault = Cpt(EpicsSignalRO, '_MPSC', kind='hinted')
    bypass = Cpt(EpicsSignal,   '_BYPS', kind='config')

    tab_whitelist = ['faulted', 'bypassed']

    @property
    def faulted(self):
        """Whether the MPS bit is faulted or not."""
        return bool(self.fault.get())

    @property
    def bypassed(self):
        """Bypass state of the MPS bit."""
        return bool(self.bypass.get())

    def _sub_to_children(self):
        """
        Subscribe to child signals
        """
        self.fault.subscribe(self._fault_change, run=False)
        self.bypass.subscribe(self._fault_change, run=False)


def mps_factory(clsname, cls,  *args, mps_prefix, veto=False,  **kwargs):
    """
    Create a new object of arbitrary class capable of storing MPS information.

    A new class identical to the provided one is created, but with additional
    attribute ``mps`` that relies upon the provided `.mps_prefix`. All other
    information is passed through to the class constructor as args and kwargs

    Parameters
    ----------
    clsname : str
        Name of new class to create.

    cls : type
        Device class to add ``mps``.

    mps_prefix : str
        Prefix for MPS subcomponent.

    veto : bool, optional
        Whether the MPS bit is capable of veto.

    args :
        Passed to device constructor.

    kwargs:
        Passed to device constructor.
    """
    comp = FCpt(MPS, mps_prefix, veto=veto)
    cls = type(clsname, (cls,), {'mps': comp})
    return cls(*args, **kwargs)


def must_be_out(in_limit, out_limit):
    """
    Logical combination of limits enforcing an out state.

    Parameters
    ----------
    in_limit : bool
        Whether the in limit is active.

    out_limit : bool
        Whether the out limit is active.

    Returns
    -------
    is_out : bool
        Whether the logical combination of the limit switch ensures that the
        device is removed.
    """

    return not in_limit and out_limit


def must_be_known(in_limit, out_limit):
    """
    Logical combination of limits enforcing a known state.

    The logic determines that we know that the device is fully inserted or
    removed, alerting the MPS if the device is stuck in an unknown state or
    broken.

    Parameters
    ----------
    in_limit : bool
        Whether the in limit is active.

    out_limit : bool
        Whether the out limit is active.

    Returns
    -------
    is_known : bool
        Whether the logical combination of the limit switch ensure that the
        device position is known.
    """

    return in_limit != out_limit


class MPSLimits(MPSBase, Device):
    """
    Logical combination of two MPS bits.

    The MPSLimits class is to determine what action is to be taken based on the
    MPS values of a device pertaining to a single device. If a device has two
    MPS values, there is certain logic that needs to be followed to determine
    whether or not the beam is allowed through.

    Parameters
    ----------
    prefix : str
        Base of the MPS PVs.

    name : str
        Name of the MPS combination.

    logic : callable
        Determine whether the MPS is faulted based on the state of each limit.
        The function signature should look like:

        .. code::

            def logic(in_limit: bool, out_limit: bool) -> bool
    """

    # Individual limits
    in_limit = Cpt(MPS, '_IN', kind='normal')
    out_limit = Cpt(MPS, '_OUT', kind='normal')

    def __init__(self, prefix, logic, **kwargs):
        self.logic = logic
        super().__init__(prefix, **kwargs)

    @property
    def faulted(self):
        """
        This property determines whether the two MPS values are faulted and
        applies a logic function depending on the states of mps_A and mps_B.
        """
        return self.logic(self.in_limit.faulted, self.out_limit.faulted)

    @property
    def bypassed(self):
        """Whether either limit is bypassed."""
        return self.in_limit.bypassed or self.out_limit.bypassed

    def _sub_to_children(self):
        self.in_limit.subscribe(self._fault_change,
                                event_type=self.in_limit.SUB_FAULT_CH)
        self.out_limit.subscribe(self._fault_change,
                                 event_type=self.out_limit.SUB_FAULT_CH)
