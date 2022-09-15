from __future__ import annotations

from typing import Dict, List, Optional, Tuple, cast

from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.signal import EpicsSignalRO
from ophyd.status import AndStatus, MoveStatus

from pcdsdevices.valve import VGC

from ..device import UnrelatedComponent as UCpt
from ..epics_motor import SmarAct
from ..interface import BaseInterface
from ..signal import PytmcSignal
from . import btms_config as btms
from .btms_config import (BtmsSourceState, BtmsState, DestinationPosition,
                          MoveError, SourcePosition)


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

    def get_delta(self, value: Optional[float] = None) -> float:
        """
        Get the delta to the nominal value.

        If ``value`` is provided, it will be used in place of the PLC-
        specified value (i.e., ``self.value``).

        Returns
        -------
        float
            (nominal - value)
        """
        if value is None:
            if not self.input_valid.get():
                raise ValueError("Input invalid: delta not available")
            value = self.value.get()

        return value - self.nominal.get()


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

    parent: DestinationConfig
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
    in_position = Cpt(
        PytmcSignal,
        "BTPS:InPosition",
        io="input",
        kind="normal",
        doc=(
            "Set if the mirror assembly for this source is in position for "
            "this laser destination"
        ),
    )

    def summarize_checks(self) -> List[str]:
        """
        Summarize all checks into a user-readable form.

        Returns
        -------
        list of str
        """
        if not self.connected:
            return ["Disconnected"]

        result = [
            f"Checks for {self.source_pos.name_and_desc} -> {self.destination_pos.name_and_desc}:"
        ]

        if not self.checks_ok.get():
            result.append("One or more checks performed by the BTPS PLC are not OK.")
        if not self.data_valid.get():
            result.append(
                "Some data on the PLC is not valid.  "
                "This could be due to a disconnected PV, unhomed motor, etc."
            )

        for desc, check in [
            ("Far field centroid X", self.far_field.centroid_x),
            ("Far field centroid Y", self.far_field.centroid_y),
            ("Near field centroid X", self.near_field.centroid_x),
            ("Near field centroid Y", self.near_field.centroid_y),
            ("Linear motor", self.linear),
            ("Rotary motor", self.rotary),
            ("Goniometer motor", self.goniometer),
        ]:
            check = cast(RangeComparison, check)
            if not check.input_valid.get():
                result.append(
                    f"{desc} data is not valid."
                )
            elif not check.in_range.get():
                low = check.low.get()
                high = check.high.get()
                value = check.value.get()
                nominal = check.nominal.get()
                inclusive = check.inclusive.get()
                less_than = "<=" if inclusive else "<"
                range_desc = (
                    f"{low} {less_than} value {less_than} {high}.  "
                    f"The nominal value is {nominal}."
                )
                if low >= high:
                    result.append(
                        f"{desc} range is not properly configured: {range_desc}"
                    )
                else:
                    result.append(
                        f"{desc} value {value} is not in range: {range_desc}"
                    )

        if not self.entry_valve_ready.get():
            result.append(
                f"The PLC reports the entry valve for {self.source_pos.name_and_desc} "
                f"is not ready"
            )

        if not self.in_position.get():
            result.append(
                f"The PLC reports {self.source_pos.name_and_desc} "
                f"is not in position"
            )

        if not self.parent.exit_valve_ready.get():
            result.append(
                f"The PLC reports the exit valve for {self.destination_pos.name_and_desc} "
                f"is not ready"
            )

        if not self.parent.yields_control.get():
            result.append(
                f"The user at {self.destination_pos.name_and_desc} "
                f"has not yielded control of the source"
            )

        if len(result) == 1:
            result.append("All checks are OK.")

        return result


class DestinationConfig(BaseInterface, Device):
    """BTPS per-destination configuration settings and state."""

    def __init__(
        self, prefix: str, destination_pos: btms.DestinationPosition, **kwargs
    ):
        self.destination_pos = destination_pos
        super().__init__(prefix, **kwargs)

    parent: BtpsState
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
    yields_control = Cpt(
        PytmcSignal,
        "BTPS:YieldsControl",
        io="output",
        kind="normal",
        doc="Destination using beam or yielding control",
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

    maintenance_mode = Cpt(
        PytmcSignal,
        "Maintenance",
        io="io",
        kind="normal",
        doc="System undergoing maintenance",
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
        PytmcSignal,
        "OPN",
        io="i",
        kind="normal",
        doc="Shutter open status",
    )

    closed_status = Cpt(
        PytmcSignal,
        "CLS",
        io="i",
        kind="normal",
        doc="Shutter closed status",
    )

    permission = Cpt(
        PytmcSignal, "LSS", io="i",
        kind="normal",
        doc="Shutter open permission status",
    )


class BtpsSourceStatus(BaseInterface, Device):
    """BTPS per-source shutter safety status."""

    def __init__(self, prefix: str, source_pos: SourcePosition, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        self.source_pos = source_pos
        super().__init__(prefix, **kwargs)

    parent: BtpsState
    source_pos: SourcePosition

    lss = Cpt(LssShutterStatus, "LST:", doc="Laser Safety System Status")
    entry_valve = Cpt(BtpsVGC, "VGC:01", doc="Source entry valve")
    linear = UCpt(SmarAct, doc="Linear Smaract stage")
    rotary = UCpt(SmarAct, doc="Rotary stage")
    goniometer = UCpt(SmarAct, doc="Goniometer stage")

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

    current_destination = Cpt(
        PytmcSignal,
        "BTPS:CurrentLD",
        io="input",
        kind="normal",
        doc="BTPS-determined current laser destination",
    )

    def set(self, dest: DestinationPosition, check: bool = True) -> AndStatus:
        """
        Move to the target destination and return a combined status for all motion.
        """
        linear_status, rotary_status, goniometer_status = self.set_with_movestatus(dest, check=check)
        return AndStatus(AndStatus(linear_status, rotary_status), goniometer_status)

    def set_with_movestatus(
        self, dest: DestinationPosition, check: bool = True
    ) -> Tuple[MoveStatus, MoveStatus, MoveStatus]:
        """
        Move to the target destination and return statuses for each motion.
        """
        if check:
            self.check_move(dest)

        config = self.parent.destinations[dest].sources[self.source_pos]

        nominal_pos = config.linear.nominal.get()
        linear_status = self.linear.set(nominal_pos)

        nominal_pos = config.rotary.nominal.get()
        rotary_status = self.rotary.set(nominal_pos)

        nominal_pos = config.goniometer.nominal.get()
        goniometer_status = self.goniometer.set(nominal_pos)
        return (linear_status, rotary_status, goniometer_status)

    def set_nominal_to_current(self) -> None:
        """
        Set the nominal positions of the BTPS data store for the current
        destination to the current motor positions.
        """
        try:
            dest_index = int(self.current_destination.get())
            dest = DestinationPosition.from_index(dest_index)
        except Exception:
            raise ValueError("Current destination invalid; unable to set nominal positions")

        config = self.parent.destinations[dest].sources[self.source_pos]

        # The current positions
        linear = self.linear.user_readback.get()
        rotary = self.rotary.user_readback.get()
        goniometer = self.goniometer.user_readback.get()

        # Set the source-to-destination data store values:
        config.linear.nominal.put(linear)
        config.rotary.nominal.put(rotary)
        config.goniometer.nominal.put(goniometer)

    def check_move(self, dest: DestinationPosition) -> None:
        """
        Check for conflicts moving this source to ``dest``.

        Parameters
        ----------
        dest : DestinationPosition
            The target destination for the source to move to.

        Raises
        ------
        MoveError
            Raises specific ``MoveError`` subclass based on the reason.
        """
        state = self.parent.to_btms_state()
        state.check_move(self.source_pos, None, dest)

    def check_move_all(self, dest: DestinationPosition) -> List[MoveError]:
        """
        Check for conflicts moving this source to ``dest``.

        Parameters
        ----------
        dest : DestinationPosition
            The target destination for the source to move to.

        Returns
        -------
        list of MoveError
            All conflicts along the motion trajectory.
        """
        state = self.parent.to_btms_state()
        return state.check_move_all(self.source_pos, None, dest)


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
        linear_prefix="LAS:BTS:MCS2:01:m1",
        rotary_prefix="LAS:BTS:MCS2:01:m2",
        goniometer_prefix="LAS:BTS:MCS2:01:m3",
        doc="Source status for LS1 (Bay 1)"
    )
    ls5 = Cpt(
        BtpsSourceStatus,
        "LTLHN:LS5:",
        source_pos=SourcePosition.ls5,
        linear_prefix="LAS:BTS:MCS2:01:m4",
        rotary_prefix="LAS:BTS:MCS2:01:m6",
        goniometer_prefix="LAS:BTS:MCS2:01:m5",
        doc="Source status for LS5 (Bay 3)"
    )
    ls8 = Cpt(
        BtpsSourceStatus,
        "LTLHN:LS8:",
        source_pos=SourcePosition.ls8,
        linear_prefix="LAS:BTS:MCS2:01:m7",
        rotary_prefix="LAS:BTS:MCS2:01:m8",
        goniometer_prefix="LAS:BTS:MCS2:01:m9",
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

    def set_source_to_destination(
        self, source: SourcePosition, dest: DestinationPosition
    ) -> AndStatus:
        """
        Move ``source`` to the target destination ``dest`` and return a combined
        status object.
        """
        return self.sources[source].set(dest)

    def set_source_to_destination_with_movestatus(
        self, source: SourcePosition, dest: DestinationPosition
    ) -> Tuple[MoveStatus, MoveStatus, MoveStatus]:
        """
        Move ``source`` to the target destination ``dest`` and return statuses
        for each motion.
        """
        return self.sources[source].set_with_movestatus(dest)

    def to_btms_state(self) -> BtmsState:
        """
        Determine the state for BTMS, indicating active source/destination pairs.

        Returns
        -------
        BtmsState
        """
        state = btms.BtmsState()
        for source in self.sources.values():
            try:
                dest_pos = DestinationPosition.from_index(
                    source.current_destination.get()
                )
            except ValueError:
                dest_pos = None

            if dest_pos is not None:
                dest = self.destinations[dest_pos]
                source_to_dest = dest.sources[source.source_pos]
                beam_status = bool(
                    source.lss.opened_status.get()
                    and bool(source_to_dest.entry_valve_ready.get())
                    and bool(dest.exit_valve_ready.get())
                )
            else:
                source_to_dest = None
                beam_status = source.lss.opened_status.get()

            state.sources[source.source_pos] = BtmsSourceState(
                source=source.source_pos,
                destination=dest_pos,
                beam_status=bool(beam_status),
            )

        for dest in self.destinations.values():
            dest_state = state.destinations[dest.destination_pos]
            dest_state.yields_control = bool(
                dest.yields_control.get()
            )

        state.maintenance_mode = bool(self.config.maintenance_mode.get())
        return state

    def status_info(self) -> Dict[str, BtmsState]:
        return {"state": self.to_btms_state()}

    def format_status_info(self, state_dict: dict):
        return str(state_dict["state"])
