"""
Ophyd devices for the acqiris digitizer systems
"""
import logging
from ophyd import EpicsSignal, EpicsSignalRO, Device
from ophyd import Component as Cpt
from ophyd import FormattedComponent as FCpt
from .interface import BaseInterface

logger = logging.getLogger(__name__)


class AcqirisChannel(Device):
    """
    Class to define a single acqiris channel.
    """

    waveform = Cpt(
        EpicsSignalRO, ":Data", kind="hinted"
    )
    v_max = Cpt(
        EpicsSignal, ":CMaxVert", kind="normal"
    )
    v_cent = Cpt(
        EpicsSignal, ":CCenter", kind="normal"
    )
    v_in = Cpt(
        EpicsSignal, ":CMinVert", kind="normal"
    )
    v_scale = Cpt(
        EpicsSignal, ":CVPerDiv", kind="normal"
    )
    bandwidth = Cpt(
        EpicsSignal, ":CBandwidth", kind="config",
        string=True
    )
    full_scale = Cpt(
        EpicsSignal, ":CFullScale", kind="config"
    )
    coupling = Cpt(
        EpicsSignal, ":CCoupling", kind="config",
        string=True
    )
    offset = Cpt(
        EpicsSignal, ":COffset", kind="config"
    )
    trig_coupling = Cpt(
        EpicsSignal, "CTrigCoupling", kind="config",
        string=True
    )
    trig_slope = Cpt(
        EpicsSignal, "CTrigSlope", kind="config",
        string=True
    )
    trig_level = Cpt(
        EpicsSignal, ":CTrigLevel1", kind="config"
    )


class Acqiris(Device, BaseInterface):
    """
    Class to define an acqiris digitizer board as constructed by the
    'GasDetDAQ' EPICS IOC. This device is used to access specific
    acqiris channels as subcomponents.

    Parameters
    ----------
    prefix : ``str``
        The PV base of the digitizer.
    platform : ``str``
        This a legacy PV segment found in the GasDetDAQ IOC.
        The default '202' applies to the HXR gas detector system.
    module : ``str``
        3-digit number representing the digitizer board,
        e.g. '240', '360'.

    """

    tab_component_names = True
    tab_whitelist = ["ch1", "ch2", "ch3", "ch4"]

    ch1 = FCpt(
        AcqirisChannel, "{self.prefix}:{self._mod_pref}1",
        kind="hinted"
    )
    ch2 = FCpt(
        AcqirisChannel, "{self.prefix}:{self._mod_pref}2",
        kind="hinted"
    )
    ch3 = FCpt(
        AcqirisChannel, "{self.prefix}:{self._mod_pref}3",
        kind="hinted"
    )
    ch4 = FCpt(
        AcqirisChannel, "{self.prefix}:{self._mod_pref}4",
        kind="hinted"
    )

    run_state = FCpt(
        EpicsSignal, "{self.prefix}:{self.module}:MDAQStatus",
        kind="config",
        string=True,
    )
    sample_interval = FCpt(
        EpicsSignal, "{self.prefix}:{self.module}:MSampInterval",
        kind="config"
    )
    delay_time = FCpt(
        EpicsSignal, "{self.prefix}:{self.module}:MDelayTime",
        kind="config"
    )
    num_samples = FCpt(
        EpicsSignal, "{self.prefix}:{self.module}:MNbrSamples",
        kind="config"
    )
    trig_source = FCpt(
        EpicsSignal,
        "{self.prefix}:{self.module}:MTriggerSource",
        kind="config",
        string=True,
    )
    trig_class = FCpt(
        EpicsSignal,
        "{self.prefix}:{self.module}:MTrigClass", kind="config",
        string=True,
    )
    samples_freq = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MSampFrequency",
        kind="config"
    )
    rate = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MEventRate",
        kind="config"
    )
    num_events = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MEventCount",
        kind="config"
    )
    num_trig_timeouts = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MTriggerTimeouts",
        kind="config"
    )
    num_truncated = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MTruncated",
        kind="config"
    )
    acq_type = FCpt(
        EpicsSignal, "{self.prefix}:{self.module}:MType",
        kind="config", string=True
    )
    acq_mode = FCpt(
        EpicsSignal, "{self.prefix}:{self.module}:MMode",
        kind="config", string=True
    )
    acq_mode_flags = FCpt(
        EpicsSignal,
        "{self.prefix}:{self.module}:MModeFlags", kind="config",
        string=True,
    )
    clock_type = FCpt(
        EpicsSignalRO,
        "{self.prefix}:{self.module}:MClockType", kind="config",
        string=True,
    )
    crate_number = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MCrateNb", kind="config"
    )
    n_adc_bits = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MNbrADCBits", kind="config"
    )
    crate_slot = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MPosInCrate", kind="config"
    )
    temp = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MTemperature_m",
        kind="config"
    )
    input_freq = FCpt(
        EpicsSignalRO, "{self.prefix}:{self.module}:MInputFrequency",
        kind="config"
    )

    def __init__(self, prefix, module, platform=None,
                 name="Acqiris", **kwargs):
        self.module = module
        self.prefix = prefix
        self.platform = platform
        if len(self.module) != 3:
            raise ValueError(
                "Acqiris 'module'"
                + " expects a 3-digit module identifier,"
                + " e.g. '240'"
            )
        self._mod_pref = self.module[:2]
        super().__init__(prefix, name=name, **kwargs)

    def start(self):
        """
        Start the acqiris DAQ
        """
        self.run_state.put(0)

    def stop(self):
        """
        Stop the acqiris DAQ
        """
        self.run_state.put(1)


class GasDet(Device):
    """
    Class to read out pulse energy from a PMT/diode as digitized
    by an acqiris in the GasDetDAQ EPICS IOC.

    Parameters
    ----------
    prefix : ``str``
        The PV base of the digitizer.
    platform : ``str``
        This a legacy PV segment found in the GasDetDAQ IOC.
        For example, '202' applies to
        the HXR gas detector system... for some reason.
    module : ``str``
        3-digit number representing the digitizer board, e.g. '240', '360'.
    channel : ``str``
        The digitizer channel.

    """

    mj = Cpt(EpicsSignalRO, ":ENRC", kind="hinted")
    time = Cpt(EpicsSignalRO, ":TIME", kind="hinted")
    cal = Cpt(EpicsSignalRO, ":CALI", kind="hinted")
    offset = Cpt(EpicsSignalRO, ":OFFS", kind="hinted")
    bg_start_index = Cpt(EpicsSignalRO, ":BSTR", kind="hinted")
    bg_stop_index = Cpt(EpicsSignalRO, ":BSTP", kind="hinted")
    bg_sum = Cpt(EpicsSignalRO, ":BSUM", kind="hinted")
    pulse_start_index = Cpt(EpicsSignalRO, ":STRT", kind="hinted")
    pulse_stop_index = Cpt(EpicsSignalRO, ":STOP", kind="hinted")
    pulse_sum = Cpt(EpicsSignalRO, ":PSUM", kind="hinted")
