"""
Module for all device related to Photon Collimators.
"""
from ophyd import Component as Cpt
from ophyd import Device

from .digital_signals import J120K


class PhotonCollimator(Device):
    """
    Photon Collimator Stub for Cooling Readback
    """
    flow_switch = Cpt(J120K, '', kind='normal',
                      doc='Device that indicates nominal PCW Flow Rate.')
