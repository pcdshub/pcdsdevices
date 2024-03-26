"""
Module for the two dimention laser coupling in TMO.
"""
from lightpath import LightpathState
from ophyd.device import Component as Cpt

from .device import GroupDevice
from .device import UpdateComponent as UpCpt
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface, LightpathMixin
from .pmps import TwinCATStatePMPS


class LaserCouplingTwoD(TwinCATStatePMPS):
    """

    Two Dimention laser coupling 2D States Setup

    Here, we specify 2 states, which we can support in an EPICS enum and 2 motors for X and Y Axes.
    """
    config = UpCpt(state_count=2, motor_count=2)


class TMOLaserCouplingTwoDimention(BaseInterface, GroupDevice, LightpathMixin):
    """

    TMO two dimention laser coupling LI2K4 class.


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

    # LaserCoupling LI2K4 x and Y
    laser_coupling = Cpt(LaserCouplingTwoD, 'LI2K4:IP1', add_prefix=(), kind='normal')
    li2k4_x = Cpt(BeckhoffAxis, ':MMS:X', doc="X-axis of lasercoupling li2k4", kind='normal')
    li2k4_y = Cpt(BeckhoffAxis, ':MMS:Y', doc="Y-axis of lasercoupling li2k4", kind='normal')
    removed = False
    transmission = 1
    SUB_STATE = 'state'

    # dummy signal, state is always the same
    lightpath_cpts = ['li2k4_x.user_readback']

    def calc_lightpath_state(self, **kwargs) -> LightpathState:
        # TODO: get real logic here, instead of legacy hard-coding
        return LightpathState(
            inserted=True,
            removed=False,
            output={self.output_branches[0]: 1}
        )
