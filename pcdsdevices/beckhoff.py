from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal


class BeckhoffECAT(Device):
    """
    Bekhoff Terminal with PVs to control ethercat state. 
    """

    state = Cpt(EpicsSignal, ":eDevState_RBV")
    request_state = Cpt(EpicsSignal, ":eReqState")
    cmd_request_state = Cpt(EpicsSignal, ":bCmdReqState")
    ecat_error = Cpt(EpicsSignal, ":bError")
    ecat_error_message = Cpt(EpicsSignal, ":sErrorMessage", string=True)
    device_description = Cpt(EpicsSignal, ":sDESC", string=True)
