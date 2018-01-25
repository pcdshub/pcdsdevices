"""
Devices that are integrated with the MPS system communicate with ACR via a
single bit summary. The results of these are published over EPICS and
interpreted by :class:`.MPS`.
"""
import logging

from ophyd import (Device, EpicsSignal, EpicsSignalRO, Component as C,
                   FormattedComponent as FC)

logger = logging.getLogger(__name__)


class MPS(Device):
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
            read_attrs = ['fault', 'bypass']
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


def mps_factory(clsname, cls,  *args, mps_prefix, veto=False,  **kwargs):
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


def must_be_open_logic(mps_A, mps_B):
    """

    This logic should analyze the two MPS classes of a device. This logic will only allow
    beam through if the device is in the open-state.

    Parameters
    ----------
    
    mps_A.fault.value: Int
    mps_B.fault.value: Int

    Returns
    -------
    
    bool
        True if successful, False otherwise


    """

    if mps_A.fault.value == 1 and mps_B.fault.value == 1:
        return False

    if mps_A.fault.value == 0 and mps_B.fault.value == 0:
        return False

    if mps_A.fault.value == 1 and mps_B.fault.value == 0:
        return False

    if mps_A.fault.value == 0 and mps_B.fault.value == 1:
        return True


def must_know_position_logic(mps_A, mps_B):
    """

    This logic should analyze the two MPS classes of a device. This logic will only allow
    beam through if both the positions of the MPS classes is known

    Parameters
    ----------
    
    mps_A.fault.value: Int
    mps_B.fault.value: Int

    Returns
    -------
    
    bool
        True if successful, False otherwise
    """
    if mps_A.fault.value == 1 and mps_B.fault.value == 1:
        return False

    if mps_A.fault.value == 0 and mps_B.fault.value == 0:
        return False

    if mps_A.fault.value == 1 and mps_B.fault.value == 0:
        return True

    if mps_A.fault.value == 0 and mps_B.fault.value == 1:
        return True


class MPSLimits(Device):
    """

    The MPSLimits class is to determine what action is to be taken based on the MPS values
    of a devicepertaining to a single device. If a device has two MPS values, there is 
    certain logic that needs to be followed to determine whether or not the beam is allowed
    through.


    Parameters
    ----------

    Device: defined in MPS class above

    Attributes
    ----------

    mps_A: the first MPS value of a Device

    mps_B: the second MPS value of a Device
   
    name: str

    logic: function
        calls one of the previously defined functions based on the Device in question
    """
    mps_A = FC(MPS, '{self.MPSA}')
    mps_B = FC(MPS, '{self.MPSB}')

    def __init__(self, mps_A, mps_B, name=None, logic=None):

        self.MPSA = mps_A
        self.MPSB = mps_B
        self.name = name
        self.logic = logic
        super().__init__('', name=name)

    @property
    def faulted(self):
    
        """

        This property determines whether the two MPS values are faulted and applies a logic 
        function depending on the states of mps_A and mps_B.

        """
        
        if not callable(self.logic):
            raise TypeError("Invalid Logic")

        return self.logic(self.mps_A, self.mps_B)

