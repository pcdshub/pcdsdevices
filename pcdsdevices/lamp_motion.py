"""
LAMP Motion Classes

This module contains classes related to the TMO-LAMP Motion System
"""

from ophyd import Component as Cpt

from .device import GroupDevice
from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class LAMP(BaseInterface, GroupDevice):
    """
    LAMP Motion Class

    This class controls motors fixed to the LAMP Motion system for the IP1
    endstation in TMO.

    Parameters
    ----------
    prefix : str
        Base PV for the LAMP motion system

    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    gas_jet_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    gas_jet_y = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    gas_jet_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')

    gas_needle_x = Cpt(BeckhoffAxis, ':MMS:04', kind='normal')
    gas_needle_y = Cpt(BeckhoffAxis, ':MMS:05', kind='normal')
    gas_needle_z = Cpt(BeckhoffAxis, ':MMS:06', kind='normal')

    sample_paddle_x = Cpt(BeckhoffAxis, ':MMS:07', kind='normal')
    sample_paddle_y = Cpt(BeckhoffAxis, ':MMS:08', kind='normal')
    sample_paddle_z = Cpt(BeckhoffAxis, ':MMS:09', kind='normal')


class LAMPMagneticBottle(BaseInterface, GroupDevice):
    """
    LAMPMagneticBottle Motion Class

    This class controls motors fixed to the LAMP Motion system for the IP1
    endstation in TMO with Magnetic Bottle configuration

    Parameters
    ----------
    prefix : str
        Base PV for the LAMP motion system

    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    gas_needle_x = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    gas_needle_y = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    gas_needle_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')
#    gas_needle_theta = Cpt(BeckhoffAxis, ':MMS:10', kind='normal')

    magnet_x = Cpt(BeckhoffAxis, ':MMS:05', kind='normal')
    magnet_y = Cpt(BeckhoffAxis, ':MMS:06', kind='normal')
    magnet_z = Cpt(BeckhoffAxis, ':MMS:04', kind='normal')


class LAMPFlowCell(BaseInterface, GroupDevice):
    """
    LAMP Motion Class

    This class controls motors fixed to the LAMP Motion system for the IP1
    endstation in TMO with the Flow Cell configuration for x454.

    Parameters
    ----------
    prefix : str
        Base PV for the LAMP motion system

    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor components
    gas_jet_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    gas_jet_y = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    gas_jet_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')

    sample_paddle_x = Cpt(BeckhoffAxis, ':MMS:07', kind='normal')
    sample_paddle_y = Cpt(BeckhoffAxis, ':MMS:08', kind='normal')
    sample_paddle_z = Cpt(BeckhoffAxis, ':MMS:09', kind='normal')

    flow_cell_x = Cpt(BeckhoffAxis, ':MMS:10', kind='normal')
    flow_cell_y = Cpt(BeckhoffAxis, ':MMS:11', kind='normal')
    flow_cell_z = Cpt(BeckhoffAxis, ':MMS:12', kind='normal')
    flow_cell_theta = Cpt(BeckhoffAxis, ':MMS:13', kind='normal')


class LAMP_LV_17(BaseInterface, GroupDevice):
    """
    LAMP Motion Class

    This class controls motors fixed to the LAMP Motion system for the IP1
    endstation in TMO with the Gas Jet, Sample Paddle, and Detector
    configuration for LV17.

    Parameters
    ----------
    prefix : str
        Base PV for the LAMP motion system

    name : str
        Alias for the device
    """
    # UI representation
    _icon = 'fa.minus-square'
    tab_component_names = True

    # Motor Component
    gas_jet_x = Cpt(BeckhoffAxis, ':MMS:01', kind='normal')
    gas_jet_y = Cpt(BeckhoffAxis, ':MMS:02', kind='normal')
    gas_jet_z = Cpt(BeckhoffAxis, ':MMS:03', kind='normal')

    sample_paddle_x = Cpt(BeckhoffAxis, ':MMS:04', kind='normal')
    sample_paddle_y = Cpt(BeckhoffAxis, ':MMS:05', kind='normal')
    sample_paddle_z = Cpt(BeckhoffAxis, ':MMS:06', kind='normal')

    detector_x = Cpt(BeckhoffAxis, ':MMS:07', kind='normal')
    detector_y = Cpt(BeckhoffAxis, ':MMS:08', kind='normal')
