"""
DREAM Motion Classes
This module contains classes related to the TMO-DREAM Motion System

"""

from ophyd import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis, SmarAct
from .interface import BaseInterface


class DREAM_MC_Y(BaseInterface, GroupDevice):
    """
    DREAM Main Chamber Motion Class
    This class controls main chamber vertical Motion system for the
    DREAM endstation in TMO.

    Parameters
    ----------
    prefix : str
        DREAM:MC
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    chamber_y = Cpt(BeckhoffAxis, ':MMS:Y', kind='normal')


class DREAM_CoilMover(BaseInterface, GroupDevice):
    """
    DREAM Motion Class
    This class controls coil motors fixed to the DREAM Motion system for the
    DREAM endstation in TMO.

    Parameters
    ----------
    prefix : str
        DREAM:COIL
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    coil_roll = Cpt(BeckhoffAxis, ':MMS:ROLL', kind='normal')
    coil_yaw = Cpt(BeckhoffAxis, ':MMS:YAW', kind='normal')


class DREAM_GasJet(BaseInterface, GroupDevice):
    """
    DREAM Motion Class
    This class controls gas jet X and Y motors fixed to the DREAM Motion system for the
    DREAM endstation in TMO.

    Parameters
    ----------
    prefix : str
        DREAM:GSJP
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    gas_jet_x = Cpt(BeckhoffAxis, ':MMS:X', kind='normal')
    gas_jet_z = Cpt(BeckhoffAxis, ':MMS:Z', kind='normal')


class DREAM_GasNozzle(BaseInterface, GroupDevice):
    """
    DREAM Motion Class
    This class controls gas nozzle X,Y and Z motors fixed to the DREAM Motion system for the
    DREAM endstation in TMO.

    Parameters
    ----------
    prefix : str
        DREAM:GSJN
    name : str, keyword-only
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    gas_nozzle_x = Cpt(BeckhoffAxis, ':MMS:X', kind='normal')
    gas_nozzle_y = Cpt(BeckhoffAxis, ':MMS:Y', kind='normal')
    gas_nozzle_z = Cpt(BeckhoffAxis, ':MMS:Z', kind='normal')


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
