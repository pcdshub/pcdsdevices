"""
Module for the liquid jet classes.
"""
from ophyd import Component as Cpt
from ophyd import Device

from .epics_motor import BeckhoffAxis
from .interface import BaseInterface


class BeckhoffJetManipulator(Device, BaseInterface):
    """Jet Manipulator controlled by Beckhoff PLC."""

    tab_component_names = True

    x = Cpt(BeckhoffAxis, ':X', kind='normal')
    y = Cpt(BeckhoffAxis, ':Y', kind='normal')
    z = Cpt(BeckhoffAxis, ':Z', kind='normal')


class BeckhoffJetSlits(Device, BaseInterface):
    """Pair of Beckhoff-controlled slits where each blade has X & Y motors."""
    tab_component_names = True

    top_x = Cpt(BeckhoffAxis, ':TOP_X', kind='normal')
    top_y = Cpt(BeckhoffAxis, ':TOP_Y', kind='normal')
    bot_x = Cpt(BeckhoffAxis, ':BOT_X', kind='normal')
    bot_y = Cpt(BeckhoffAxis, ':BOT_Y', kind='normal')


class BeckhoffJet(Device, BaseInterface):
    """
    Full liquid jet setup controlled by a Beckhoff PLC.

    This includes three axes for the jet manipulator, two axes for each of two
    slits, and a single axis for the detector. Each of their PVs will be
    inferred from the base prefix.

    Parameters
    ----------
    prefix : str, optional
        Liquid jet base PV.

    name : str
        A name to refer to the device.
    """

    tab_component_names = True

    jet = Cpt(BeckhoffJetManipulator, ':JET', kind='normal')
    ss = Cpt(BeckhoffJetSlits, ':SLIT', kind='normal')
    vh_epix_x = Cpt(BeckhoffAxis, ':DET:X', kind='normal')
