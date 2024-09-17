"""TMO sample calibration foil to work with spectrometer"""
from lightpath import LightpathState
from ophyd.device import Component as Cpt

from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface, LightpathMixin
from .pmps import TwinCATStatePMPS


class CalibrationAxis(TwinCATStatePMPS):
    """
    Sample calibration 1D State Setup
    Here, we specify 7 states, and 1 motor, for Y
    axe.Add OUT states IN, total is 8
    """
    config = UpCpt(state_count=8, motor_count=1)


class SCaFoil(BaseInterface, GroupDevice, LightpathMixin):
    """
    TMO PMPS1D sample calibration class.
    Parameters:
    -----------
    prefix : str
        Base PV for the motion system
    name : str
        Alias for the device
    """
    # UI Representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Sample calibration Y axis

    pf_state = Cpt(CalibrationAxis, ':STATE', kind='normal')
    pf_y = Cpt(BeckhoffAxis, ':MMS:Y', doc="Y-axis of photo filter pa1k4", kind='normal')
    removed = False
    transmission = 1
    SUB_STATE = 'state'

    # dummy signal, state is always the same
    lightpath_cpts = ['cali_foil.user_readback']

    def calc_lightpath_state(self, **kwargs) -> LightpathState:
        return LightpathState(
            inserted=True,
            removed=False,
            output={self.output_branches[0]: 1}
        )
