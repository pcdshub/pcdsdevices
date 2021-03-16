"""
Module for the Sample Delivery System and related devices.
"""
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal

from .device import UnrelatedComponent as UCpt
from .interface import BaseInterface
from .signal import PytmcSignal


class M3BasePLCDevice(BaseInterface, Device):
    """
    Base device for M3 SDS PLC devices.

    For ethercat diagnostics and other general purpose values.
    Currently only holds the sync unit, to tell if the cluster is alive.
    """

    status = Cpt(PytmcSignal, ':IO:SyncUnitOK', io='i', kind='normal')


class ViciValve(BaseInterface, Device):
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


class Selector(M3BasePLCDevice):
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

    shaker1 = Cpt(PytmcSignal, ':Shaker:01:Ctrl', io='o', kind='normal')
    shaker2 = Cpt(PytmcSignal, ':Shaker:02:Ctrl', io='o', kind='normal')
    shaker3 = Cpt(PytmcSignal, ':Shaker:03:Ctrl', io='o', kind='normal')
    shaker4 = Cpt(PytmcSignal, ':Shaker:04:Ctrl', io='o', kind='normal')

    valve1 = Cpt(ViciValve, ':Valve:01', name='ViciValve1')
    valve2 = Cpt(ViciValve, ':Valve:02', name='ViciValve2')

    lock = Cpt(PytmcSignal, ':ValvesLockRequest', io='o', kind='normal')
    unlock = Cpt(PytmcSignal, ':ValvesUnlockRequest', io='o', kind='normal')
    locked = Cpt(PytmcSignal, ':ValvesLocked', io='i', kind='normal')
    synced = Cpt(PytmcSignal, ':ValvesSynced', io='i', kind='normal')

    sync_req_pos = Cpt(PytmcSignal, ':ValveSyncReqPos', io='o', kind='normal')
    sync_curr_pos = Cpt(PytmcSignal, ':ValveSyncCurrentPos', io='i',
                        kind='normal')


class CoolerShaker(BaseInterface, Device):
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


class HPLC(BaseInterface, Device):
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
        super().__init__(prefix, name=name, **kwargs)


class PropAir(BaseInterface, Device):
    """
    A Proportionair pressure regulator used by the Pressure Control Module.

    Parameters
    ----------
    prefix : str
        The base PV for the Proportionair.

    name : str
        A name for the device.
    """

    pressure = Cpt(PytmcSignal, ':Pressure', io='i', kind='normal')
    enabled = Cpt(PytmcSignal, ':Enable', io='io', kind='normal')
    setpoint = Cpt(PytmcSignal, ':Setpoint', io='io', kind='normal')
    low_limit = Cpt(PytmcSignal, ':LowLimit', io='io', kind='normal')
    high_limit = Cpt(PytmcSignal, ':HighLimit', io='io', kind='normal')


class PCM(M3BasePLCDevice):
    """
    A Pressure Control Module for the sample delivery system.

    Parameters
    ----------
    prefix : str
        The base PV for the Pressure Control Module.

    name : str
        A name for the device.
    """

    propair1 = Cpt(PropAir, ':PropAir:01', name='PropAir1')
    propair2 = Cpt(PropAir, ':PropAir:02', name='PropAir2')


class IntegratedFlow(BaseInterface, Device):
    """
    A single flow for the FlowIntegrator.

    Parameters
    ----------
    start_prefix : str
        Starting volume of the flow.

    used_prefix : str
        Flow rate of the flow.

    flow1_time_prefix : str
        Estimated depletion time of the flow.
    """

    start = UCpt(EpicsSignal)
    used = UCpt(EpicsSignal)
    time = UCpt(EpicsSignal)

    def __init__(self, prefix, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, name=name, **kwargs)


class FlowIntegrator(BaseInterface, Device):
    """
    A Flow Integrator for the sample delivery system.

    Parameters
    ----------
    name : str
        A name for the device.

    integrator_source_prefix : str

    flow_source_prefix : str

    names_prefix : str

    flow1_start_prefix : str
        Starting volume of flow 1.

    flow1_used_prefix : str
        Flow rate of flow 1.

    flow1_time_prefix : str
        Estimated depletion time of flow 1.

    flow2_start_prefix : str
        Starting volume of flow 2.

    flow2_used_prefix : str
        Flow rate of flow 2.

    flow2_time_prefix : str
        Estimated depletion time of flow 2.

    flow3_start_prefix : str
        Starting volume of flow 3.

    flow3_used_prefix : str
        Flow rate of flow 3.

    flow3_time_prefix : str
        Estimated depletion time of flow 3.

    flow4_start_prefix : str
        Starting volume of flow 4.

    flow4_used_prefix : str
        Flow rate of flow 4.

    flow4_time_prefix : str
        Estimated depletion time of flow 4.

    flow5_start_prefix : str
        Starting volume of flow 5.

    flow5_used_prefix : str
        Flow rate of flow 5.

    flow5_time_prefix : str
        Estimated depletion time of flow 5.

    flow6_start_prefix : str
        Starting volume of flow 6.

    flow6_used_prefix : str
        Flow rate of flow 6.

    flow6_time_prefix : str
        Estimated depletion time of flow 6.

    flow7_start_prefix : str
        Starting volume of flow 7.

    flow7_used_prefix : str
        Flow rate of flow 7.

    flow7_time_prefix : str
        Estimated depletion time of flow 7.

    flow8_start_prefix : str
        Starting volume of flow 8.

    flow8_used_prefix : str
        Flow rate of flow 8.

    flow8_time_prefix : str
        Estimated depletion time of flow 8.

    flow9_start_prefix : str
        Starting volume of flow 9.

    flow9_used_prefix : str
        Flow rate of flow 9.

    flow9_time_prefix : str
        Estimated depletion time of flow 9.

    flow10_start_prefix : str
        Starting volume of flow 10.

    flow10_used_prefix : str
        Flow rate of flow 10.

    flow10_time_prefix : str
        Estimated depletion time of flow 10.
    """

    integrator_source = UCpt(EpicsSignal)
    flow_source = UCpt(EpicsSignal)
    names = UCpt(EpicsSignal)

    flow1 = UCpt(IntegratedFlow)
    flow2 = UCpt(IntegratedFlow)
    flow3 = UCpt(IntegratedFlow)
    flow4 = UCpt(IntegratedFlow)
    flow5 = UCpt(IntegratedFlow)
    flow6 = UCpt(IntegratedFlow)
    flow7 = UCpt(IntegratedFlow)
    flow8 = UCpt(IntegratedFlow)
    flow9 = UCpt(IntegratedFlow)
    flow10 = UCpt(IntegratedFlow)

    def __init__(self, *, name, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__('', name=name, **kwargs)


class ManifoldValve(BaseInterface, Device):
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


class GasManifold(M3BasePLCDevice):
    """
    A Gas Manifold as used in the sample delivery system.

    Parameters
    ----------
    prefix : str
        The base PV for the Gas Manifold.

    name : str
        A name for the device.
    """

    valve1 = Cpt(ManifoldValve, ':Valve:01', name='ManifoldValve1')
    valve2 = Cpt(ManifoldValve, ':Valve:02', name='ManifoldValve1')
    valve3 = Cpt(ManifoldValve, ':Valve:03', name='ManifoldValve1')
    valve4 = Cpt(ManifoldValve, ':Valve:04', name='ManifoldValve1')
    valve5 = Cpt(ManifoldValve, ':Valve:05', name='ManifoldValve1')
    valve6 = Cpt(ManifoldValve, ':Valve:06', name='ManifoldValve1')
    valve7 = Cpt(ManifoldValve, ':Valve:07', name='ManifoldValve1')
    valve8 = Cpt(ManifoldValve, ':Valve:08', name='ManifoldValve1')
