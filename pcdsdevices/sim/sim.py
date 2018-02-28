"""
Simulated device classes
"""
from ophyd import Device

from .signal import FakeSignal
from .component import Component


class SimDevice(Device):
    """
    Class to house components and methods common to all simulated devices.
    """
    sim_x = Component(FakeSignal, value=0)
    sim_y = Component(FakeSignal, value=0)
    sim_z = Component(FakeSignal, value=0)
