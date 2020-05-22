"""
Standard classes for LCLS Energy Monitors.
"""
import logging

from ophyd import Component as Cpt
from ophyd import Device
from ophyd.signal import SignalRO

from .interface import BaseInterface

logger = logging.getLogger(__name__)


class GEM(Device, BaseInterface):
    """
    Gas Energy Monitor from the LUSI project.

    A base class for a Gas Energy Monitor.

    Parameters
    ----------
    prefix : str
        Full GEM base PV.

    name : str
        Name to refer to the GEM.
    """

    not_implemented = Cpt(SignalRO, name="Not Implemented",
                          value="Not Implemented", kind='normal')


class GMD(Device, BaseInterface):
    """
    Gas Monitor Detector, installed in the LCLS-II XTES project.

    A base class for a GMD.

    Parameters
    ----------
    prefix : str
        Full GMD base PV.

    name : str
        Name to refer to the GMD.
    """

    not_implemented = Cpt(SignalRO, name="Not Implemented",
                          value="Not Implemented", kind='normal')


class XGMD(Device, BaseInterface):
    """
    X Gas Monitor Detector (2nd generation GMD).

    A base class for an XGMD, installed in the LCLS-II XTES project.

    Parameters
    ----------
    prefix : str
        Full XGMD base PV.

    name : str
        Name to refer to the XGMD.
    """

    not_implemented = Cpt(SignalRO, name="Not Implemented",
                          value="Not Implemented", kind='normal')
