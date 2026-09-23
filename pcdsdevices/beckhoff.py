from ophyd.device import Device
from ophyd.signal import EpicsSignal
from ophyd.device import Component as Cpt

class BeckhoffECAT(Device):
    state = Cpt(EpicsSignal, ":eDevState_RBV")
    request_state = Cpt(EpicsSignal, ":eReqState")
    cmd_request_state = Cpt(EpicsSignal, ":bCmdReqState")
    ecat_error = Cpt(EpicsSignal, ":bError")
    ecat_error_message = Cpt(EpicsSignal, ":sErrorMessage", string=True)
    device_description = Cpt(EpicsSignal, ":sDESC", string=True)

