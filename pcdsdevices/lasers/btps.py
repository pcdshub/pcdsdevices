from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignalRO

from ..interface import BaseInterface
from ..signal import PytmcSignal
from ..valve import VGC


class ReadOnlyValve(BaseInterface, Device):
    alm_rst = Cpt(EpicsSignalRO, ':ALM_RST_RBV', kind='normal')
    at_vac_hys = Cpt(EpicsSignalRO, ':AT_VAC_HYS_RBV', kind='normal')
    at_vac_sp = Cpt(EpicsSignalRO, ':AT_VAC_SP_RBV', kind='normal')
    dis_dpilk = Cpt(EpicsSignalRO, ':Dis_DPIlk_RBV', kind='normal')
    eps_ok = Cpt(EpicsSignalRO, ':EPS_OK_RBV', kind='normal')
    error = Cpt(EpicsSignalRO, ':ERROR_RBV', kind='normal')
    err_difpres = Cpt(EpicsSignalRO, ':ERR_DifPres_RBV', kind='normal')
    err_ext = Cpt(EpicsSignalRO, ':ERR_Ext_RBV', kind='normal')
    err_sp = Cpt(EpicsSignalRO, ':ERR_SP_RBV', kind='normal')
    errmsg = Cpt(EpicsSignalRO, ':ErrMsg_RBV', kind='normal', string=True)
    ff_reset = Cpt(EpicsSignalRO, ':FF_Reset_RBV', kind='normal')
    force_opn = Cpt(EpicsSignalRO, ':FORCE_OPN_RBV', kind='normal')
    hyst_perc = Cpt(EpicsSignalRO, ':HYST_PERC_RBV', kind='normal')
    mps_fault_ok = Cpt(EpicsSignalRO, ':MPS_FAULT_OK_RBV', kind='normal')
    mps_ok = Cpt(EpicsSignalRO, ':MPS_OK_RBV', kind='normal')
    opn_sw = Cpt(EpicsSignalRO, ':OPN_SW_RBV', kind='normal')
    ovrd_on = Cpt(EpicsSignalRO, ':OVRD_ON_RBV', kind='normal')


class RangeComparison(BaseInterface, Device):
    """BTPS single value range comparison check."""
    value = Cpt(
        PytmcSignal,
        "Value",
        io="input",
        kind="hinted",
        doc="Current value from the control system",
    )
    in_range = Cpt(
        PytmcSignal,
        "InRange",
        io="input",
        kind="hinted",
        doc="Is the value currently in range?",
    )
    input_valid = Cpt(
        PytmcSignal,
        "Valid",
        io="input",
        kind="normal",
        doc="Is the value considered valid?",
    )

    # Configuration settings:
    low = Cpt(
        PytmcSignal,
        "Low",
        io="io",
        kind="normal",
        doc="Configurable lower bound for the value range",
    )
    high = Cpt(
        PytmcSignal,
        "High",
        io="io",
        kind="normal",
        doc="Configurable upper bound for the value range",
    )
    inclusive = Cpt(
        PytmcSignal,
        "Inclusive",
        io="io",
        kind="normal",
        doc="Is the value comparison exclusive or inclusive?",
    )


class CentroidConfig(BaseInterface, Device):
    """BTPS camera centroid range comparison."""
    centroid_x = Cpt(RangeComparison, "CenterX:", kind="normal", doc="Centroid X range")
    centroid_y = Cpt(RangeComparison, "CenterY:", kind="normal", doc="Centroid Y range")


class SourceConfig(BaseInterface, Device):
    """BTPS per-(source, destination) configuration settings and state."""
    name_ = Cpt(
        PytmcSignal,
        "Name",
        io="input",
        kind="normal",
        doc="Source name",
        string=True,
    )
    far_field = Cpt(CentroidConfig, "FF", kind="normal", doc="Far field centroid")
    near_field = Cpt(CentroidConfig, "NF", kind="normal", doc="Near field centroid")

    goniometer = Cpt(RangeComparison, "Goniometer:", kind="normal", doc="Goniometer stage")
    linear = Cpt(RangeComparison, "Linear:", kind="normal", doc="Linear stage")
    rotary = Cpt(RangeComparison, "Rotary:", kind="normal", doc="Rotary stage")
    checks_ok = Cpt(
        PytmcSignal, "ChecksOK", io="input", kind="normal",
        doc="Check summary"
    )
    data_valid = Cpt(
        PytmcSignal, "Valid", io="input", kind="normal",
        doc="Data validity summary"
    )

    # TODO: good or bad idea?
    entry_valve = Cpt(ReadOnlyValve, "Valve", kind="normal", doc="Source entry valve")


class DestinationConfig(BaseInterface, Device):
    """BTPS per-destination configuration settings and state."""
    name_ = Cpt(
        PytmcSignal,
        "Name",
        io="input",
        kind="normal",
        doc="Destination name",
        string=True,
    )
    source1 = Cpt(SourceConfig, "SRC:01:", doc="Settings for source 1")
    source3 = Cpt(SourceConfig, "SRC:03:", doc="Settings for source 3")
    source4 = Cpt(SourceConfig, "SRC:04:", doc="Settings for source 4")
    exit_valve = Cpt(ReadOnlyValve, "DestValve", doc="Exit valve for the destination")


class GlobalConfig(BaseInterface, Device):
    """BTPS global configuration settings."""
    max_frame_time = Cpt(
        PytmcSignal,
        "MaxFrameTime",
        io="io",
        kind="normal",
        doc="Maximum time between frame updates in seconds to be considered 'valid' data",
    )


class BtpsState(BaseInterface, Device):
    """
    Beam Transport Protection System (BTPS) State
    """
    config = Cpt(GlobalConfig, "Config:", doc="Global configuration")

    dest1 = Cpt(DestinationConfig, "DEST:01:", doc="Destination 1")
    dest2 = Cpt(DestinationConfig, "DEST:02:", doc="Destination 2")
    dest3 = Cpt(DestinationConfig, "DEST:03:", doc="Destination 3")
    dest4 = Cpt(DestinationConfig, "DEST:04:", doc="Destination 4")
    dest5 = Cpt(DestinationConfig, "DEST:05:", doc="Destination 5")
    dest6 = Cpt(DestinationConfig, "DEST:06:", doc="Destination 6")
    dest7 = Cpt(DestinationConfig, "DEST:07:", doc="Destination 7")
