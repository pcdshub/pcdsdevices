"""
DREAM Motion Classes
This module contains classes related to the TMO-DREAM Motion System

"""

from ophyd import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis, SmarAct
from .interface import BaseInterface


class TMODream(BaseInterface, GroupDevice):
    """
    Dream Motion Class

    This class controls motors fixed to the dream in-air Motion system for the Dream
    endstation in TMO with the Gas Nozzle, Gas jet, Coil and Main Chamber Y.

    Parameters
    ----------
    prefix : str
        Base PV for the DREAM motion system
        DREAM:
    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    gas_nozzle_x = Cpt(BeckhoffAxis, ":GSJN:MMS:X", doc="dream gas nozzle x axis", kind="normal")
    gas_nozzle_y = Cpt(BeckhoffAxis, ":GSJN:MMS:Y", doc="dream gas nozzle y axis", kind="normal")
    gas_nozzle_z = Cpt(BeckhoffAxis, ":GSJN:MMS:Z", doc="dream gas nozzle z axis", kind="normal")
    gas_jet_x = Cpt(BeckhoffAxis, ":GSJP:MMS:X", doc="dream gas jet x axis", kind="normal")
    gas_jet_z = Cpt(BeckhoffAxis, ":GSJP:MMS:Z", doc="dream gas jet z axis", kind="normal")
    coil_roll = Cpt(BeckhoffAxis, ":COIL:MMS:ROLL", doc="dream coil roll axis", kind="normal")
    coil_yaw = Cpt(BeckhoffAxis, ":COIL:MMS:YAW", doc="dream coil yaw axis", kind="normal")
    chamber_y = Cpt(BeckhoffAxis, ":MC:MMS:Y", doc="dream main chamber Y axis", kind="normal")


class DREAM_SL3K4(BaseInterface, GroupDevice):
    """
    DREAM Motion Class
    This class controls DREAM SL3K4 SmarAct based scatter slit

    Parameters
    ----------
    prefix : str
        TMO:DREAM:MCS2:01
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    top = Cpt(SmarAct, ':m7', kind='normal')
    bottom = Cpt(SmarAct, ':m12', kind='normal')
    north = Cpt(SmarAct, ':m9', kind='normal')
    south = Cpt(SmarAct, ':m8', kind='normal')


class DREAM_Sample_Paddle(BaseInterface, GroupDevice):
    """
    DREAM Motion Class
    This class controls sample paddle X,Y, Z, and Ret motors fixed to the DREAM Motion system for the
    DREAM endstation in TMO.
    Parameters
    ----------
    prefix : str
        TMO:DREAM:MCS2:01
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True
    # Motor components
    x = Cpt(SmarAct, ':m2', kind='normal')
    y = Cpt(SmarAct, ':m1', kind='normal')
    z = Cpt(SmarAct, ':m4', kind='normal')
    ret = Cpt(SmarAct, ':m3', kind='normal')
