"""
Module for the Sample Delivery System and related devices.
"""
from ophyd.device import Device
from ophyd.signal import EpicsSignal

from .component import UnrelatedComponent as UCpt


class Selector(Device):
    """
    A Selector for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the name of the device and
        the PVs of all the selector components.

    Attributes
    ----------
    remote_control : EpicsSignal
        Remote control enabled.

    status : EpicsSignal
        Connection status for selector.

    flow : EpicsSignal
        Flow.

    flowstate : EpicsSignal
        State of the flow.

    flowtype : EpicsSignal
        Type of the flow.

    FM_rb : EpicsSignal

    FM_reset : EpicsSignal

    FM : EpicsSignal

    names_button : EpicsSignal

    couple_button : EpicsSignal

    names1 : EpicsSignal

    names2 : EpicsSignal

    shaker1 : EpicsSignal
        Shaker 1.

    shaker2 : EpicsSignal
        Shaker 2.

    shaker3 : EpicsSignal
        Shaker 3.

    shaker4 : EpicsSignal
        Shaker 4.
    """

    # also appears on pressure controller screen?
    remote_control = UCpt(EpicsSignal)
    status = UCpt(EpicsSignal)

    flow = UCpt(EpicsSignal)
    flowstate = UCpt(EpicsSignal)
    flowtype = UCpt(EpicsSignal)

    FM_rb = UCpt(EpicsSignal)
    FM_reset = UCpt(EpicsSignal)
    FM = UCpt(EpicsSignal)

    names_button = UCpt(EpicsSignal)
    couple_button = UCpt(EpicsSignal)
    names1 = UCpt(EpicsSignal)
    names2 = UCpt(EpicsSignal)

    shaker1 = UCpt(EpicsSignal)
    shaker2 = UCpt(EpicsSignal)
    shaker3 = UCpt(EpicsSignal)
    shaker4 = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class CoolerShaker(Device):
    """
    A Cooler/Shaker for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the PVs of all the cooler/shaker components.
    name : str
        The device name.

    Attributes
    ----------
    temperature1 : EpicsSignal
        Temperature of 1.

    SP1 : EpicsSignal
        Set point of 1.

    set_SP1 : EpicsSignal
        Set the set point for 1.

    current1 : EpicsSignal
        Current for 1.

    temperature2 : EpicsSignal
        Temperature of 2.

    SP2 : EpicsSignal
        Set point of 2.

    set_SP2 : EpicsSignal
        Set the set point of 2.

    current2 : EpicsSignal
        Current of 2.

    reboot : EpicsSignal
        Reboot the cooler/shaker.
    """

    temperature1 = UCpt(EpicsSignal)
    SP1 = UCpt(EpicsSignal)
    set_SP1 = UCpt(EpicsSignal)
    current1 = UCpt(EpicsSignal)

    temperature2 = UCpt(EpicsSignal)
    SP2 = UCpt(EpicsSignal)
    set_SP2 = UCpt(EpicsSignal)
    current2 = UCpt(EpicsSignal)

    reboot = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class HPLC(Device):
    """
    An HPLC for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the PVs of all the HPLC components.

    name : str
        The device name.

    Attributes
    ----------
    status : EpicsSignal
        Status of the HPLC.

    run : EpicsSignal
        Run the HPLC.

    flowrate : EpicsSignal
        Flow rate of the HPLC.

    set_flowrate : EpicsSignal
        Set the flow rate of the HPLC.

    flowrate_SP : EpicsSignal
        Set point for the flow rate.

    pressure : EpicsSignal
        Pressure in the HPLC.

    pressure_units : EpicsSignal
        Units for the pressure.

    set_max_pressure : EpicsSignal
        Set the maximum pressure.

    max_pressure : EpicsSignal
        Maximum pressure.

    clear_error : EpicsSignal
        Clear errors.
    """

    status = UCpt(EpicsSignal)
    run = UCpt(EpicsSignal)

    flowrate = UCpt(EpicsSignal)
    set_flowrate = UCpt(EpicsSignal)
    flowrate_SP = UCpt(EpicsSignal)

    pressure = UCpt(EpicsSignal)
    pressure_units = UCpt(EpicsSignal)
    set_max_pressure = UCpt(EpicsSignal)
    max_pressure = UCpt(EpicsSignal)

    clear_error = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(name=name, **kwargs)


class PressureController(Device):
    """
    An Pressure Controller for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the PVs of all the pressure
        controller components.

    name : str
        The device name.

    Attributes
    ----------
    status : EpicsSignal
        Connection status of pressure controller.

    pressure1 : EpicsSignal
        Pressure of 1.

    enabled1 : EpicsSignal
        Is 1 enabled.

    limit1 : EpicsSignal
        High pressure limit of 1.

    SP1 : EpicsSignal
        Pressure set point of 1.

    pressure2 : EpicsSignal
        Pressure of 2.

    enabled2 : EpicsSignal
        Is 2 enabled.

    limit2 : EpicsSignal
        High pressure limit of 2.

    SP2 : EpicsSignal
        Pressure set point of 2.
    """

    status = UCpt(EpicsSignal)

    pressure1 = UCpt(EpicsSignal)
    enabled1 = UCpt(EpicsSignal)
    limit1 = UCpt(EpicsSignal)
    SP1 = UCpt(EpicsSignal)

    pressure2 = UCpt(EpicsSignal)
    enabled2 = UCpt(EpicsSignal)
    limit2 = UCpt(EpicsSignal)
    SP2 = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class FlowIntegrator(Device):
    """
    An Flow Integrator for the sample delivery system.

    Parameters
    ----------
    pvs : str dict
        A dictionary containing the PVs of all the flow integrator components.

    name : str
        The device name.


    Attributes
    ----------
    integrator_source: EpicsSignal

    flow_source : EpicsSignal

    names : EpicsSignal
        Names of.

    start1 : EpicsSignal
        Starting volume of 1.

    used1 : EpicsSignal
        Flow of 1.

    time1 : EpicsSignal
        Estimated depletion time of 1.

    start2 : EpicsSignal
        Starting volume of 2.

    used2 : EpicsSignal
        Flow of 2.

    time2 : EpicsSignal
        Estimated depletion time of 2.

    start3 : EpicsSignal
        Starting volume of 3.

    used3 : EpicsSignal
        Flow of 3.

    time3 : EpicsSignal
        Estimated depletion time of 3.

    start4 : EpicsSignal
        Starting volume of 4.

    used4 : EpicsSignal
        Flow of 4.

    time4 : EpicsSignal
        Estimated depletion time of 4.

    start5 : EpicsSignal
        Starting volume of 5.

    used5 : EpicsSignal
        Flow of 5.

    time5 : EpicsSignal
        Estimated depletion time of 5.

    start6 : EpicsSignal
        Starting volume of 6.

    used6 : EpicsSignal
        Flow of 6.

    time6 : EpicsSignal
        Estimated depletion time of 6.

    start7 : EpicsSignal
        Starting volume of 7.

    used7 : EpicsSignal
        Flow of 7.

    time7 : EpicsSignal
        Estimated depletion time of 7.

    start8 : EpicsSignal
        Starting volume of 8.

    used8 : EpicsSignal
        Flow of 8.

    time8 : EpicsSignal
        Estimated depletion time of 8.

    start9 : EpicsSignal
        Starting volume of 9.

    used9 : EpicsSignal
        Flow of 9.

    time9 : EpicsSignal
        Estimated depletion time of 9.

    start10 : EpicsSignal
        Starting volume of 10.

    used10 : EpicsSignal
        Flow of 10.

    time10 : EpicsSignal
        Estimated depletion time of 10.

    """

    integrator_source = UCpt(EpicsSignal)
    flow_source = UCpt(EpicsSignal)
    names = UCpt(EpicsSignal)

    start1 = UCpt(EpicsSignal)
    used1 = UCpt(EpicsSignal)
    time1 = UCpt(EpicsSignal)

    start2 = UCpt(EpicsSignal)
    used2 = UCpt(EpicsSignal)
    time2 = UCpt(EpicsSignal)

    start3 = UCpt(EpicsSignal)
    used3 = UCpt(EpicsSignal)
    time3 = UCpt(EpicsSignal)

    start4 = UCpt(EpicsSignal)
    used4 = UCpt(EpicsSignal)
    time4 = UCpt(EpicsSignal)

    start5 = UCpt(EpicsSignal)
    used5 = UCpt(EpicsSignal)
    time5 = UCpt(EpicsSignal)

    start6 = UCpt(EpicsSignal)
    used6 = UCpt(EpicsSignal)
    time6 = UCpt(EpicsSignal)

    start7 = UCpt(EpicsSignal)
    used7 = UCpt(EpicsSignal)
    time7 = UCpt(EpicsSignal)

    start8 = UCpt(EpicsSignal)
    used8 = UCpt(EpicsSignal)
    time8 = UCpt(EpicsSignal)

    start9 = UCpt(EpicsSignal)
    used9 = UCpt(EpicsSignal)
    time9 = UCpt(EpicsSignal)

    start10 = UCpt(EpicsSignal)
    used10 = UCpt(EpicsSignal)
    time10 = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class SDS(Device):
    """
    Sample delivery system.

    Parameters
    ----------
    devices : dict
        A dictionary of dictionaries containing the devices to be made and
        their PV names. The dictionary key is a string, one of the following:
        {'selector', 'cooler_shaker', 'hplc', 'pressure_controller',
        'flow_integrator'}
        The values of the dictionary, are also dictionaries. These are passed
        to the new device, allowing parameters such as PV names to be
        specified.

    Attributes
    ----------
    SDS_devices : list
        List containing all the devices that are in the sample delivery system.
    """

    selector = UCpt(Selector)
    cooler_shaker = UCpt(CoolerShaker)
    hplc = UCpt(HPLC)
    pressure_controller = UCpt(PressureController)
    flow_integrator = UCpt(FlowIntegrator)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)
