from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal

from pcdsdevices.valve import VGC

from ..device import UnrelatedComponent as UCpt
from ..interface import BaseInterface
from ..signal import PytmcSignal


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
    nominal = Cpt(
        PytmcSignal,
        "Nominal",
        io="io",
        kind="normal",
        doc="The nominal value",
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
    centroid_x = Cpt(
        RangeComparison,
        "CenterX:",
        kind="normal",
        doc="Centroid X range"
    )
    centroid_y = Cpt(
        RangeComparison,
        "CenterY:",
        kind="normal",
        doc="Centroid Y range"
    )


class SourceConfig(BaseInterface, Device):
    """BTPS per-(source, destination) configuration settings and state."""
    name_ = Cpt(
        PytmcSignal,
        "BTPS:Name",
        io="input",
        kind="normal",
        doc="Source name",
        string=True,
    )
    far_field = Cpt(
        CentroidConfig,
        "BTPS:FF",
        kind="normal",
        doc="Far field centroid"
    )
    near_field = Cpt(
        CentroidConfig,
        "BTPS:NF",
        kind="normal",
        doc="Near field centroid"
    )
    goniometer = Cpt(
        RangeComparison,
        "BTPS:Goniometer:",
        kind="normal",
        doc="Goniometer stage"
    )
    linear = Cpt(
        RangeComparison,
        "BTPS:Linear:",
        kind="normal",
        doc="Linear stage",
    )
    rotary = Cpt(
        RangeComparison,
        "BTPS:Rotary:",
        kind="normal",
        doc="Rotary stage",
    )
    entry_valve_ready = Cpt(
        PytmcSignal,
        "BTPS:EntryValveReady",
        io="input",
        kind="normal",
        doc="Entry valve is open and ready",
    )

    checks_ok = Cpt(
        PytmcSignal, "BTPS:ChecksOK", io="input", kind="normal",
        doc="Check summary"
    )
    data_valid = Cpt(
        PytmcSignal, "BTPS:Valid", io="input", kind="normal",
        doc="Data validity summary"
    )


class DestinationConfig(BaseInterface, Device):
    """BTPS per-destination configuration settings and state."""
    name_ = Cpt(
        PytmcSignal,
        "BTPS:Name",
        io="input",
        kind="normal",
        doc="Destination name",
        string=True,
    )
    exit_valve_ready = Cpt(
        PytmcSignal,
        "BTPS:ExitValveReady",
        io="input",
        kind="normal",
        doc="Exit valve is open and ready",
    )
    ls1 = Cpt(SourceConfig, "LS1:", doc="Settings for source LS1 (bay 1)")
    ls5 = Cpt(SourceConfig, "LS5:", doc="Settings for source LS5 (bay 3)")
    ls8 = Cpt(SourceConfig, "LS8:", doc="Settings for source LS8 (bay 4)")
    exit_valve = Cpt(VGC, "VGC:01", kind="normal", doc="Destination exit valve")


class GlobalConfig(BaseInterface, Device):
    """BTPS global configuration settings."""
    max_frame_time = Cpt(
        PytmcSignal,
        "MaxFrameTime",
        io="io",
        kind="normal",
        doc=(
            "Maximum time between frame updates in seconds to be considered "
            "'valid' data"
        ),
    )

    min_pixel_sum_change = Cpt(
        PytmcSignal,
        "MinPixelChange",
        io="io",
        kind="normal",
        doc=(
            "Minimal change (in pixels) for camera image sum to be considered "
            "valid"
        ),
    )


class LssShutterStatus(BaseInterface, Device):
    """BTPS per-source shutter status per the laser safety system."""
    open_request = Cpt(
        PytmcSignal,
        "REQ",
        io="io",
        kind="normal",
        doc="User request to open/close shutter",
    )

    opened_status = Cpt(
        # PytmcSignal, "OPN", io="i",
        EpicsSignal, "OPN_RBV",   # TODO: for testing
        kind="normal",
        doc="Shutter open status",
    )

    closed_status = Cpt(
        # PytmcSignal, "CLS", io="i",
        EpicsSignal, "CLS_RBV",   # TODO: for testing
        kind="normal",
        doc="Shutter closed status",
    )

    permission = Cpt(
        # PytmcSignal, "LSS", io="i",
        EpicsSignal, "LSS_RBV",   # TODO: for testing
        kind="normal",
        doc="Shutter open permission status",
    )


class ShutterSafety(BaseInterface, Device):
    """BTPS per-source shutter safety status."""

    def __init__(self, prefix: str, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, **kwargs)

    lss = Cpt(LssShutterStatus, "LST:", doc="Laser Safety System Status")
    entry_valve = Cpt(VGC, "VGC:01", kind="normal", doc="Source entry valve")

    open_request = Cpt(
        PytmcSignal,
        "BTPS:UserOpen",
        io="io",
        kind="normal",
        doc="User request to open/close shutter",
    )

    latched_error = Cpt(
        PytmcSignal,
        "BTPS:Error",
        io="input",
        kind="normal",
        doc="Latched error",
    )

    acknowledge = Cpt(
        PytmcSignal,
        "BTPS:Acknowledge",
        io="io",
        kind="normal",
        doc="User acknowledgement of latched fault",
    )

    override = Cpt(
        PytmcSignal,
        "BTPS:Override",
        io="io",
        kind="normal",
        doc="BTPS advanced override mode",
    )

    lss_open_request = Cpt(
        PytmcSignal,
        "BTPS:LSS:OpenRequest",
        io="input",
        kind="normal",
        doc="Output request to LSS open shutter",
    )

    safe_to_open = Cpt(
        PytmcSignal,
        "BTPS:Safe",
        io="input",
        kind="normal",
        doc="BTPS safe to open indicator",
    )


class BtpsState(BaseInterface, Device):
    """
    Beam Transport Protection System (BTPS) State.
    """
    config = Cpt(
        GlobalConfig,
        "LTLHN:BTPS:Config:",
        doc="Global BTPS configuration",
    )

    ls1 = Cpt(
        ShutterSafety,
        "LTLHN:LS1:",
        doc="Source Shutter LS1 (Bay 1)"
    )
    ls5 = Cpt(
        ShutterSafety,
        "LTLHN:LS5:",
        doc="Source Shutter LS5 (Bay 3)"
    )
    ls8 = Cpt(
        ShutterSafety,
        "LTLHN:LS8:",
        doc="Source Shutter LS8 (Bay 4)"
    )

    # Commented-out destinations are not currently installed:
    # ld1 = Cpt(DestinationConfig, "LTLHN:LD1:", doc="Destination LD1")
    ld2 = Cpt(DestinationConfig, "LTLHN:LD2:", doc="Destination LD2")
    # ld3 = Cpt(DestinationConfig, "LTLHN:LD3:", doc="Destination LD3")
    ld4 = Cpt(DestinationConfig, "LTLHN:LD4:", doc="Destination LD4")
    # ld5 = Cpt(DestinationConfig, "LTLHN:LD5:", doc="Destination LD5")
    ld6 = Cpt(DestinationConfig, "LTLHN:LD6:", doc="Destination LD6")
    # ld7 = Cpt(DestinationConfig, "LTLHN:LD7:", doc="Destination LD7")
    ld8 = Cpt(DestinationConfig, "LTLHN:LD8:", doc="Destination LD8")
    ld9 = Cpt(DestinationConfig, "LTLHN:LD9:", doc="Destination LD9")
    ld10 = Cpt(DestinationConfig, "LTLHN:LD10:", doc="Destination LD10")
    # ld11 = Cpt(DestinationConfig, "LTLHN:LD11:", doc="Destination LD11")
    # ld12 = Cpt(DestinationConfig, "LTLHN:LD12:", doc="Destination LD12")
    # ld13 = Cpt(DestinationConfig, "LTLHN:LD13:", doc="Destination LD13")
    ld14 = Cpt(DestinationConfig, "LTLHN:LD14:", doc="Destination LD14")
