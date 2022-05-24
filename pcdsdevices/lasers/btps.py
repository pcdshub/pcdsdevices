from ophyd.device import Component as Cpt
from ophyd.device import Device

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
        "Name",
        io="input",
        kind="normal",
        doc="Source name",
        string=True,
    )
    far_field = Cpt(
        CentroidConfig,
        "FF",
        kind="normal",
        doc="Far field centroid"
    )
    near_field = Cpt(
        CentroidConfig,
        "NF",
        kind="normal",
        doc="Near field centroid"
    )
    goniometer = Cpt(
        RangeComparison,
        "Goniometer:",
        kind="normal",
        doc="Goniometer stage"
    )
    linear = Cpt(RangeComparison, "Linear:", kind="normal", doc="Linear stage")
    rotary = Cpt(RangeComparison, "Rotary:", kind="normal", doc="Rotary stage")
    entry_valve_ready = Cpt(
        PytmcSignal,
        "EntryValveReady",
        io="input",
        kind="normal",
        doc="Entry valve is open and ready",
    )

    checks_ok = Cpt(
        PytmcSignal, "ChecksOK", io="input", kind="normal",
        doc="Check summary"
    )
    data_valid = Cpt(
        PytmcSignal, "Valid", io="input", kind="normal",
        doc="Data validity summary"
    )

    # TODO: good or bad idea?
    # entry_valve = Cpt(VGC, "Valve", kind="normal", doc="Source entry valve")


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
    # exit_valve = Cpt(VGC, "DestValve", doc="Exit valve for the destination")
    exit_valve_ready = Cpt(
        PytmcSignal,
        "ExitValveReady",
        io="input",
        kind="normal",
        doc="Exit valve is open and ready",
    )


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


class ShutterSafety(BaseInterface, Device):
    """BTPS per-source shutter safety status."""
    open_request = Cpt(
        PytmcSignal,
        "UserOpen",
        io="io",
        kind="normal",
        doc="User request to open/close shutter",
    )

    latched_error = Cpt(
        PytmcSignal,
        "Error",
        io="input",
        kind="normal",
        doc="Latched error",
    )

    acknowledge = Cpt(
        PytmcSignal,
        "Acknowledge",
        io="io",
        kind="normal",
        doc="User acknowledgement of latched fault",
    )

    override = Cpt(
        PytmcSignal,
        "Override",
        io="io",
        kind="normal",
        doc="BTPS advanced override mode",
    )

    lss_open_request = Cpt(
        PytmcSignal,
        "LSS:OpenRequest",
        io="input",
        kind="normal",
        doc="Output request to LSS open shutter",
    )

    safe_to_open = Cpt(
        PytmcSignal,
        "Safe",
        io="input",
        kind="normal",
        doc="BTPS safe to open indicator",
    )


class BtpsState(BaseInterface, Device):
    """
    Beam Transport Protection System (BTPS) State
    """
    config = Cpt(GlobalConfig, "Config:", doc="Global configuration")

    shutter1 = Cpt(ShutterSafety, "Shutter:01:", doc="Source Shutter 1")
    shutter3 = Cpt(ShutterSafety, "Shutter:03:", doc="Source Shutter 3")
    shutter4 = Cpt(ShutterSafety, "Shutter:04:", doc="Source Shutter 4")

    dest1 = Cpt(DestinationConfig, "DEST:01:", doc="Destination 1")
    dest2 = Cpt(DestinationConfig, "DEST:02:", doc="Destination 2")
    dest3 = Cpt(DestinationConfig, "DEST:03:", doc="Destination 3")
    dest4 = Cpt(DestinationConfig, "DEST:04:", doc="Destination 4")
    dest5 = Cpt(DestinationConfig, "DEST:05:", doc="Destination 5")
    dest6 = Cpt(DestinationConfig, "DEST:06:", doc="Destination 6")
    dest7 = Cpt(DestinationConfig, "DEST:07:", doc="Destination 7")
