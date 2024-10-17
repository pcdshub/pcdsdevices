"""
Module for all device related to Photon Collimators.
"""
from ophyd import Component as Cpt
from ophyd import Device

from .analog_signals import FDQ
from .digital_signals import J120K


class PhotonCollimator(Device):
    """
    Photon Collimator Stub for Cooling Switch Readback
    """
    flow_switch = Cpt(J120K, '', kind='normal',
                      doc='Device that indicates nominal PCW Flow Rate.')


class PhotonCollimatorFDQ(Device):
    """
    Photon Collimator Stub for Cooling Meter Readback
    """
    flow_meter = Cpt(FDQ, '', kind='normal',
                     doc='Device that measures PCW Flow Rate.')
