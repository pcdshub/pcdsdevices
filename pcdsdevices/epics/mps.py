"""
Devices that are integrated with the MPS system communicate with ACR via a
single bit summary. The results of these are published over EPICS and
interpreted by :class:`.MPS`. 
"""
############
# Standard #
############
import logging

###############
# Third Party #
###############
from ..interface import MPSInterface

##########
# Module #
##########
from ophyd      import Device
from .signal    import EpicsSignal, EpicsSignalRO
from .component import Component as C, FormattedComponent as FC

logger = logging.getLogger(__name__)


class MPS(Device, metaclass=MPSInterface):
    """
    Class to interpret MPS information

    The intention of this class is to be used as a sub-component of a device.
    There are three major attributes of each MPS bit that are relevant to
    operations; :attr:`.faulted` , :attr:`.bypassed` and :attr:`.veto_capable`.
    The first is the most obvious, when the device is faulted it reports as
    such to the MPS system. However, how this is actually interpreted by the
    MPS is determined by whether the bit is bypassed, and if there is a
    ``veto`` device upstream such that the fault can be safely ignored. The
    bypassed state is reported through EPICS as well but unfortunately whether
    a device is considered capable of  "veto-ing" or is vetoed by another
    device is not broadcast by EPICS so this is held within this device and the
    ``lighpath`` module

    Parameters
    ----------
    prefix : str

    name : str, optional

    veto : bool, optional
        Whether or not the  

    read_attrs : list, optional
    """
    fault  = C(EpicsSignalRO, '_MPSC')
    bypass = C(EpicsSignal,   '_BYPS')

    SUB_FAULT_CH  = 'sub_mps_faulted'
    _default_sub  = SUB_FAULT_CH

    def __init__(self, prefix, *, name=None, veto=False,
                 read_attrs=None, **kwargs):
        self._veto = veto
        #Default read attributes
        if read_attrs is None:
            read_attrs = ['faulted', 'tripped']
        #Device initialization
        super().__init__(prefix, name=name, read_attrs=read_attrs, **kwargs)
        #Subscribe state change callback
        self.fault.subscribe(self._fault_change, run=False)
        self.bypass.subscribe(self._fault_change, run=False)

    @property
    def faulted(self):
        """
        Whether the MPS bit is faulted or not

        This interprets both the fault and bypass bit to determine if the fault
        will actually affect the beam
        """
        if self.bypassed:
            return False

        return bool(self.fault.value)

    @property
    def veto_capable(self):
        """
        Whether the device causes downstream faults to be ignored
        """
        return self._veto

    @property
    def bypassed(self):
        """
        Bypass state of the MPS bit
        """
        return bool(self.bypass.value)

    def _fault_change(self, *args, **kwargs):
        """
        Callback when the state of the MPS bit has changed
        """
        kwargs.pop('sub_type', None)
        self._run_subs(sub_type=self.SUB_FAULT_CH, **kwargs)


def mps_factory(clsname, cls,  *args, mps_prefix=None, veto=False,  **kwargs):
    """
    Create a new object of arbitrary class capable of storing MPS information

    A new class identical to the provided one is created, but with additional
    attribute `mps` that relies upon the provided `mps_prefix`. All other
    information is passed through to the class constructor as args and kwargs

    Parameters
    ----------
    clsname : str
        Name of new class to create

    cls :
        Device class to add `mps`

    mps_prefix : str
        Prefix for MPS subcomponent

    veto : bool, optional
        Whether the MPS bit is capable of veto

    args :
        Passed to device constructor

    kwargs:
        Passed to device constructor
    """
    comp = FC(MPS, mps_prefix, veto=veto)
    cls  = type(clsname, (cls,), {'mps' : comp})
    return cls(*args, **kwargs)
