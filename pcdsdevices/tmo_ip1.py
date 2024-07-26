"TMO sample calibration foil to work with spectrometer"
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
    Here, we specify 5 states, and 1 motor, for Y
    axe.
    """
    config = UpCpt(state_count=5, motor_count=1)


class SCaliFoil(BaseInterface, GroupDevice, LightpathMixin):
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

    # Sample calibration Y axe
    cali_foil = Cpt(CalibrationAxis, 'AT2K4:IP1:STATE', add_prefix=(), kind='normal')
    cali_foil_y = Cpt(BeckhoffAxis, ':MMS', doc="Y-axis of sample caliration at2k4", kind='normal')
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
