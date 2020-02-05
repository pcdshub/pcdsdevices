"""
Standard classes for LCLS Gas Energy Monitor
"""
import logging

from ophyd import Device
from ophyd.signal import SignalRO
from ophyd import Component as Cpt

from .interface import BaseInterface

logger = logging.getLogger(__name__)


class GEM(Device, BaseInterface):
    """
    Gas Energy Monitor

    A base class for a Gas Energy Monitor

    Parameters
    ----------
    prefix : ``str``
        Full GEM base PV

    name : ``str``
        Alias for the GEM
    """
    not_implemented = Cpt(SignalRO, name="Not Implemented", value="Not Implemented", kind='normal')

