from ophyd import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class LiquidJet(BaseInterface, GroupDevice):
    """
    Liquid jet motion class.

    This class controls the axis for the liquid jet setups
    """
    tab_component_names = True
    #_icon = 'fa.minus-square'
    #_icon = 'fa.clock-o'

    # jet motors
    jet_x = Cpt(BeckhoffAxis, ':JET:X', kind='hinted')
    jet_y = Cpt(BeckhoffAxis, ':JET:Y', kind='hinted')
    jet_z = Cpt(BeckhoffAxis, ':JET:Z', kind='hinted')

    # det motor
    det_x = Cpt(BeckhoffAxis, ':DET:X', kind='hinted')

    # slits motors
    s_top_x = Cpt(BeckhoffAxis, ':SS:TOP_X', kind='hinted')
    s_top_y = Cpt(BeckhoffAxis, ':SS:TOP_Y', kind='hinted')
    s_bot_x = Cpt(BeckhoffAxis, ':SS:BOT_X', kind='hinted')
    s_bot_y = Cpt(BeckhoffAxis, ':SS:BOT_Y', kind='hinted')
