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
    remote_control_prefix : str
        Remote control enabled.

    status_prefix : str
        Connection status for selector.

    flow_prefix : str
        Flow.

    flowstate_prefix : str
        State of the flow.

    flowtype_prefix : str
        Type of the flow.

    FM_rb_prefix : str

    FM_reset_prefix : str

    FM_prefix : str

    names_button_prefix : str

    couple_button_prefix : str

    names1_prefix : str

    names2_prefix : str

    shaker1_prefix : str
        Shaker 1.

    shaker2_prefix : str
        Shaker 2.

    shaker3_prefix : str
        Shaker 3.

    shaker4_prefix : str
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
    name : str
        The device name.

    temperature1_prefix : str
        Temperature of 1.

    SP1_prefix : str
        Set point of 1.

    set_SP1_prefix : str
        Set the set point for 1.

    current1_prefix : str
        Current for 1.

    temperature2_prefix : str
        Temperature of 2.

    SP2_prefix : str
        Set point of 2.

    set_SP2_prefix : str
        Set the set point of 2.

    current2_prefix : str
        Current of 2.

    reboot_prefix : str
        PV which reboots the cooler/shaker.
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
    name : str
        The device name.

    status_prefix : str
        Status of the HPLC.

    run_prefix : str
        Run the HPLC.

    flowrate_prefix : str
        Flow rate of the HPLC.

    set_flowrate_prefix : str
        Set the flow rate of the HPLC.

    flowrate_SP_prefix : str
        Set point for the flow rate.

    pressure_prefix : str
        Pressure in the HPLC.

    pressure_units_prefix : str
        Units for the pressure.

    set_max_pressure_prefix : str
        Set the maximum pressure.

    max_pressure_prefix : str
        Maximum pressure.

    clear_error_prefix : str
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
    A Pressure Controller for the sample delivery system.

    Parameters
    ----------
    name : str
        The device name.

    status_prefix : str
        Connection status of pressure controller.

    pressure1_prefix : str
        Pressure of 1.

    enabled1_prefix : str
        Is 1 enabled.

    limit1_prefix : str
        High pressure limit of 1.

    SP1_prefix : str
        Pressure set point of 1.

    pressure2_prefix : str
        Pressure of 2.

    enabled2_prefix : str
        Is 2 enabled.

    limit2_prefix : str
        High pressure limit of 2.

    SP2_prefix : str
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
    name : str
        The device name.

    integrator_source_prefix : str

    flow_source_prefix : str

    names_prefix : str
        Names of.

    start1_prefix : str
        Starting volume of 1.

    used1_prefix : str
        Flow of 1.

    time1_prefix : str
        Estimated depletion time of 1.

    start2_prefix : str
        Starting volume of 2.

    used2_prefix : str
        Flow of 2.

    time2_prefix : str
        Estimated depletion time of 2.

    start3_prefix : str
        Starting volume of 3.

    used3_prefix : str
        Flow of 3.

    time3_prefix : str
        Estimated depletion time of 3.

    start4_prefix : str
        Starting volume of 4.

    used4_prefix : str
        Flow of 4.

    time4_prefix : str
        Estimated depletion time of 4.

    start5_prefix : str
        Starting volume of 5.

    used5_prefix : str
        Flow of 5.

    time5_prefix : str
        Estimated depletion time of 5.

    start6_prefix : str
        Starting volume of 6.

    used6_prefix : str
        Flow of 6.

    time6_prefix : str
        Estimated depletion time of 6.

    start7_prefix : str
        Starting volume of 7.

    used7_prefix : str
        Flow of 7.

    time7_prefix : str
        Estimated depletion time of 7.

    start8_prefix : str
        Starting volume of 8.

    used8_prefix : str
        Flow of 8.

    time8_prefix : str
        Estimated depletion time of 8.

    start9_prefix : str
        Starting volume of 9.

    used9_prefix : str
        Flow of 9.

    time9_prefix : str
        Estimated depletion time of 9.

    start10_prefix : str
        Starting volume of 10.

    used10_prefix : str
        Flow of 10.

    time10_prefix : str
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
    Sample Delivery System.

    Contains each of the SDS devices as a `~ophyd.device.Component`.
    This takes a LOT of prefix parameters. Prefixes should be passed in as
    keyword arguments with the keyword names following `UnrelatedComponent`
    naming standard where the devices are `selector`, `cooler_shaker`, `hplc`,
    `pressure_controller`, and `flow_integrator`.
    """

    selector = UCpt(Selector)
    cooler_shaker = UCpt(CoolerShaker)
    hplc = UCpt(HPLC)
    pressure_controller = UCpt(PressureController)
    flow_integrator = UCpt(FlowIntegrator)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)
