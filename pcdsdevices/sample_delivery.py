"""
Module for the Sample Delivery System and related devices.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal

from .component import UnrelatedComponent as UCpt
from .signal import PytmcSignal


class ViciValve(Device):
    """
    A Vici Valve as used in the SDS Selector.

    Parameters
    ----------
    prefix : str
        The base PV for the Selector.

    name : str
        A name for the device.
    """

    req_pos = Cpt(PytmcSignal, ':ReqPos', io='io', kind='normal')
    curr_pos = Cpt(PytmcSignal, ':CurrentPos', io='i', kind='normal')


class Selector(Device):
    """
    A Selector for the sample delivery system.

    This class uses the M3 variant of selector, including two Sensirion liquid
    flowmeters, a Bronkhorst mass flow meter, and two 12-position Vici valves.

    Parameters
    ----------
    prefix : str
        The base PV for the Selector.

    name : str
        A name for the device.
    """

    status = Cpt(PytmcSignal, ':IO:SyncUnitOK', io='i', kind='normal')

    sampleFM_flow = Cpt(PytmcSignal, ':SampleFM:Flow', io='i', kind='normal')
    sampleFM_state = Cpt(PytmcSignal, ':SampleFM:State', io='i',
                         kind='normal')
    sampleFM_reset = Cpt(PytmcSignal, ':SampleFM:Reset', io='o', kind='normal')
    sampleFM_mode = Cpt(PytmcSignal, ':SampleFM:Mode', io='o', kind='normal')
    sampleFM_mode_rb = Cpt(PytmcSignal, ':SampleFM:ModeRb', io='i',
                           kind='normal')

    sheathFM_flow = Cpt(PytmcSignal, ':SheathFM:Flow', io='i', kind='normal')
    sheathFM_state = Cpt(PytmcSignal, ':SheathFM:State', io='i',
                         kind='normal')
    sheathFM_reset = Cpt(PytmcSignal, ':SheathFM:Reset', io='o', kind='normal')
    sheathFM_mode = Cpt(PytmcSignal, ':SheathFM:Mode', io='o', kind='normal')
    sheathFM_mode_rb = Cpt(PytmcSignal, ':SheathFM:ModeRb', io='i',
                           kind='normal')

    massFM_unit = Cpt(PytmcSignal, ':MassFM:Unit', io='i', kind='normal')
    massFM_flow = Cpt(PytmcSignal, ':MassFM:Flow', io='i', kind='normal')

    # TODO: Add CXI:SDS:SEL1:SYNC_RES_REQ and other aux records

    shaker1 = Cpt(PytmcSignal, ':Shaker1:Ctrl', io='o', kind='normal')
    shaker2 = Cpt(PytmcSignal, ':Shaker2:Ctrl', io='o', kind='normal')
    shaker3 = Cpt(PytmcSignal, ':Shaker3:Ctrl', io='o', kind='normal')
    shaker4 = Cpt(PytmcSignal, ':Shaker4:Ctrl', io='o', kind='normal')

    valve1 = Cpt(ViciValve, ':Valve:01', name='ViciValve1')
    valve2 = Cpt(ViciValve, ':Valve:02', name='ViciValve2')

    lock = Cpt(PytmcSignal, ':ValvesLockRequest', io='o', kind='normal')
    unlock = Cpt(PytmcSignal, ':ValvesUnlockRequest', io='o', kind='normal')
    locked = Cpt(PytmcSignal, ':ValvesLocked', io='io', kind='normal')
    synced = Cpt(PytmcSignal, ':ValvesSynced', io='io', kind='normal')

    sync_req_pos = Cpt(PytmcSignal, ':ValveSyncReqPos', io='o', kind='normal')
    sync_curr_pos = Cpt(PytmcSignal, ':ValveSyncCurrentPos', io='i',
                        kind='normal')


class CoolerShaker(Device):
    """
    A Cooler/Shaker for the sample delivery system.

    Parameters
    ----------
    prefix : str
        The base PV for the Pressure Controller.

    name : str
        A name for the device.

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
    prefix : str
        The base PV for the Pressure Controller.

    name : str
        A name for the device.

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
    prefix : str
        The base PV for the Pressure Controller.

    name : str
        A name for the device.
    """

    status = Cpt(PytmcSignal, ':IO:SyncUnitOK', io='i', kind='normal')

    pressure1 = Cpt(PytmcSignal, ':PropAir1:Pressure', io='i', kind='normal')
    enabled1 = Cpt(PytmcSignal, ':PropAir1:Enable', io='io', kind='normal')
    SP1 = Cpt(PytmcSignal, ':PropAir1:Setpoint', io='io', kind='normal')
    low_limit1 = Cpt(PytmcSignal, ':PropAir1:LowLimit', io='io', kind='normal')
    high_limit1 = Cpt(PytmcSignal, ':PropAir1:HighLimit', io='io',
                      kind='normal')

    pressure2 = Cpt(PytmcSignal, ':PropAir2:Pressure', io='i', kind='normal')
    enabled2 = Cpt(PytmcSignal, ':PropAir2:Enable', io='io', kind='normal')
    SP2 = Cpt(PytmcSignal, ':PropAir2:Setpoint', io='io', kind='normal')
    low_limit2 = Cpt(PytmcSignal, ':PropAir2:LowLimit', io='io', kind='normal')
    high_limit2 = Cpt(PytmcSignal, ':PropAir2:HighLimit', io='io',
                      kind='normal')


class FlowIntegrator(Device):
    """
    A Flow Integrator for the sample delivery system.

    Parameters
    ----------
    prefix : str
        The base PV for the Flow Integrator.

    name : str
        A name for the device.

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


class ManifoldValve(Device):
    """
    A single valve as present in the SDS Gas Manifold.

    Parameters
    ----------
    prefix : str
        The base PV for the Gas Manifold.

    name : str
        A name for the device.
    """

    open = Cpt(PytmcSignal, ':Open', io='o', kind='normal')
    open_do = Cpt(PytmcSignal, ':OpenDO', io='i', kind='normal')
    open_sw = Cpt(PytmcSignal, ':OpenSW', io='i', kind='normal')
    interlocked = Cpt(PytmcSignal, ':Ilk', io='i', kind='normal')


class GasManifold(Device):
    """
    A Gas Manifold as used in the sample delivery system.

    Parameters
    ----------
    prefix : str
        The base PV for the Gas Manifold.

    name : str
        A name for the device.
    """

    status = Cpt(PytmcSignal, ':IO:SyncUnitOK', io='i', kind='normal')

    valve1 = Cpt(ManifoldValve, ':Valve:01', name='ManifoldValve1')
    valve2 = Cpt(ManifoldValve, ':Valve:02', name='ManifoldValve1')
    valve3 = Cpt(ManifoldValve, ':Valve:03', name='ManifoldValve1')
    valve4 = Cpt(ManifoldValve, ':Valve:04', name='ManifoldValve1')
    valve5 = Cpt(ManifoldValve, ':Valve:05', name='ManifoldValve1')
    valve6 = Cpt(ManifoldValve, ':Valve:06', name='ManifoldValve1')
    valve7 = Cpt(ManifoldValve, ':Valve:07', name='ManifoldValve1')
    valve8 = Cpt(ManifoldValve, ':Valve:08', name='ManifoldValve1')
