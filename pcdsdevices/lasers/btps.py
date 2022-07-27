from typing import Dict, Optional

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO

from pcdsdevices.valve import VGC

from ..device import UnrelatedComponent as UCpt
from ..interface import BaseInterface
from ..signal import PytmcSignal
from . import btms_config as btms
from .btms_config import (BtmsSourceState, BtmsState, DestinationPosition,
                          SourcePosition)


class BtpsVGC(VGC):
    """
    VGC subclass with 'valve_position' component added.
    """
    # TODO: this may be pushed into ValveBase, but need to check with others
    # first
    valve_position = Cpt(
        EpicsSignalRO,
        ':POS_STATE_RBV',
        kind='hinted',
        string=True,
        doc='Ex: OPEN, CLOSED, MOVING, INVALID, OPEN_F'
    )


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

    def get_delta(self) -> float:
        """
        Get the delta to the nominal value.

        Returns
        -------
        float
            (nominal - value)
        """
        if not self.input_valid.get():
            raise ValueError("Input invalid: delta not available")

        return self.value.get() - self.nominal.get()


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


class SourceToDestinationConfig(BaseInterface, Device):
    """BTPS per-(source, destination) configuration settings and state."""

    def __init__(
        self,
        prefix: str,
        source_pos: SourcePosition,
        destination_pos: Optional[btms.DestinationPosition] = None,
        **kwargs
    ):
        self.source_pos = source_pos
        super().__init__(prefix, **kwargs)

        if destination_pos is None:
            try:
                destination_pos = self.parent.destination_pos
            except AttributeError:
                raise RuntimeError(
                    "destination_pos must be passed as a kwarg or available "
                    "on the parent device"
                )

        assert isinstance(destination_pos, DestinationPosition)
        self.destination_pos = destination_pos

    source_pos: SourcePosition
    destination_pos: btms.DestinationPosition

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

    def __init__(
        self, prefix: str, destination_pos: btms.DestinationPosition, **kwargs
    ):
        self.destination_pos = destination_pos
        super().__init__(prefix, **kwargs)

    destination_pos: btms.DestinationPosition
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
    ls1 = Cpt(
        SourceToDestinationConfig,
        "LS1:",
        source_pos=SourcePosition.ls1,
        doc="Settings for source LS1 (bay 1) to this destination",
    )
    ls5 = Cpt(
        SourceToDestinationConfig,
        "LS5:",
        source_pos=SourcePosition.ls5,
        doc="Settings for source LS5 (bay 3) to this destination",
    )
    ls8 = Cpt(
        SourceToDestinationConfig,
        "LS8:",
        source_pos=SourcePosition.ls8,
        doc="Settings for source LS8 (bay 4) to this destination",
    )
    exit_valve = Cpt(BtpsVGC, "VGC:01", kind="normal", doc="Destination exit valve")

    @property
    def sources(self) -> Dict[SourcePosition, SourceToDestinationConfig]:
        """

        Returns
        -------
        Dict[SourcePosition, SourceToDestinationConfig]

        """
        return {
            source.source_pos: source
            for source in (self.ls1, self.ls5, self.ls8)
        }


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


class BtpsSourceStatus(BaseInterface, Device):
    """BTPS per-source shutter safety status."""

    def __init__(self, prefix: str, source_pos: SourcePosition, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        self.source_pos = source_pos
        super().__init__(prefix, **kwargs)

    source_pos: SourcePosition

    lss = Cpt(LssShutterStatus, "LST:", doc="Laser Safety System Status")
    entry_valve = Cpt(BtpsVGC, "VGC:01", kind="normal", doc="Source entry valve")

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sources = {
            source.source_pos: source
            for source in (self.ls1, self.ls5, self.ls8)
        }

        self.destinations = {
            dest.destination_pos: dest
            for dest in (
                self.ld2,
                # self.ld3,
                self.ld4,
                # self.ld5,
                self.ld6,
                # self.ld7,
                self.ld8,
                self.ld9,
                self.ld10,
                # self.ld11,
                # self.ld12,
                # self.ld13,
                self.ld14,
            )
        }

    sources: Dict[SourcePosition, BtpsSourceStatus]
    destinations: Dict[btms.DestinationPosition, DestinationConfig]

    config = Cpt(
        GlobalConfig,
        "LTLHN:BTPS:Config:",
        doc="Global BTPS configuration",
    )

    ls1 = Cpt(
        BtpsSourceStatus,
        "LTLHN:LS1:",
        source_pos=SourcePosition.ls1,
        doc="Source status for LS1 (Bay 1)"
    )
    ls5 = Cpt(
        BtpsSourceStatus,
        "LTLHN:LS5:",
        source_pos=SourcePosition.ls5,
        doc="Source status for LS5 (Bay 3)"
    )
    ls8 = Cpt(
        BtpsSourceStatus,
        "LTLHN:LS8:",
        source_pos=SourcePosition.ls8,
        doc="Source status for LS8 (Bay 4)"
    )

    # Commented-out destinations are not currently installed:
    # ld1 = Cpt(DestinationConfig, "LTLHN:LD1:", doc="Destination LD1", destination_pos=DestinationPosition.ld1)
    ld2 = Cpt(
        DestinationConfig,
        "LTLHN:LD2:",
        doc="Destination LD2",
        destination_pos=DestinationPosition.ld2,
    )
    # ld3 = Cpt(DestinationConfig, "LTLHN:LD3:", doc="Destination LD3", destination_pos=DestinationPosition.ld3)
    ld4 = Cpt(
        DestinationConfig,
        "LTLHN:LD4:",
        doc="Destination LD4",
        destination_pos=DestinationPosition.ld4,
    )
    # ld5 = Cpt(DestinationConfig, "LTLHN:LD5:", doc="Destination LD5", destination_pos=DestinationPosition.ld5)
    ld6 = Cpt(
        DestinationConfig,
        "LTLHN:LD6:",
        doc="Destination LD6",
        destination_pos=DestinationPosition.ld6,
    )
    # ld7 = Cpt(DestinationConfig, "LTLHN:LD7:", doc="Destination LD7", destination_pos=DestinationPosition.ld7)
    ld8 = Cpt(
        DestinationConfig,
        "LTLHN:LD8:",
        doc="Destination LD8",
        destination_pos=DestinationPosition.ld8,
    )
    ld9 = Cpt(
        DestinationConfig,
        "LTLHN:LD9:",
        doc="Destination LD9",
        destination_pos=DestinationPosition.ld9,
    )
    ld10 = Cpt(
        DestinationConfig,
        "LTLHN:LD10:",
        doc="Destination LD10",
        destination_pos=DestinationPosition.ld10,
    )
    # ld11 = Cpt(DestinationConfig, "LTLHN:LD11:", doc="Destination LD11", destination_pos=DestinationPosition.ld11)
    # ld12 = Cpt(DestinationConfig, "LTLHN:LD12:", doc="Destination LD12", destination_pos=DestinationPosition.ld12)
    # ld13 = Cpt(DestinationConfig, "LTLHN:LD13:", doc="Destination LD13", destination_pos=DestinationPosition.ld13)
    ld14 = Cpt(
        DestinationConfig,
        "LTLHN:LD14:",
        doc="Destination LD14",
        destination_pos=DestinationPosition.ld14,
    )

    def to_btms_state(self) -> BtmsState:
        """
        Determine the state for BTMS, indicating active source/destination pairs.

        Returns
        -------
        BtmsState
        """
        state = btms.BtmsState()
        for source in self.sources.values():
            dest_configs = [
                dest.sources[source.source_pos]
                for dest in self.destinations.values()
            ]
            try:
                deltas = {
                    conf.linear.get_delta(): conf.destination_pos
                    for conf in dest_configs
                }
                dest_pos = deltas[min(deltas)]
            except ValueError:
                dest_pos = None

            if dest_pos is not None:
                dest = self.destinations[dest_pos]
                dest_valve_ready = bool(dest.exit_valve_ready.get())
            else:
                dest_valve_ready = False

            state.sources[source.source_pos] = BtmsSourceState(
                source=source.source_pos,
                destination=dest_pos,
                beam_status=bool(
                    source.lss.opened_status.get()
                    and source.entry_valve_ready.get()
                    and dest_valve_ready
                ),
            )

        return state
