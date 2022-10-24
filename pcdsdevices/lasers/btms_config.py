from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


POSITION_DIAGRAM = """

             LD8   LD9  LD10  LD11  LD12  LD13  LD14
            <========================================= LS5
        LS1 =========================================>
            <========================================= LS6
        LS2 =========================================>
            <========================================= LS7
        LS3 =========================================>
            <========================================= LS8
        LS4 =========================================>
               LD1   LD2    LD3  LD4   LD5   LD6   LD7

"""


class _PositionDiagram:
    """
    An internal diagram helper for showing the current btps state in
    hutch-python.

    Used by BtmsState.
    """
    COL_WIDTH = 3
    STAGE_CHAR = "*"
    BEAM_CHAR_UP = "^"
    BEAM_CHAR_DOWN = "v"

    def __init__(self):
        self.text = POSITION_DIAGRAM

    def _find_line_col(self, text: str) -> Tuple[int, int]:
        """Get the line and column of ``text``."""
        for lineno, line in enumerate(self.text.splitlines()):
            if text in line:
                return lineno, line.index(text)
        raise ValueError(f"{text} not found")

    def _fill(
        self, character: str, first_line: int, last_line: int, col1: int, col2: int
    ) -> str:
        """Fill lines first_line to last_line from col1 to col2 with ``character``."""
        assert len(character) == 1
        results = []
        if first_line > last_line:
            first_line, last_line = last_line, first_line
        if col1 > col2:
            col1, col2 = col2, col1
        for lineno, line in enumerate(self.text.splitlines()):
            if first_line <= lineno <= last_line:
                line_chars = list(line)
                line_chars[col1:col2] = [character] * (col2 - col1)
                line = "".join(line_chars)
            results.append(line)
        return "\n".join(results)

    def add_source(
        self, source: SourcePosition, dest: DestinationPosition, beam_status: bool
    ) -> None:
        """
        Add a source to the diagram.

        Parameters
        ----------
        source : SourcePosition
            The source position.
        dest : DestinationPosition
            The destination that the source is positioned at.
        beam_status : bool
            True if the beam is reportedly enabled.
        """
        source_line, _ = self._find_line_col(source.value)
        dest_line, dest_col = self._find_line_col(dest.value)

        self.text = self._fill(
            self.STAGE_CHAR,
            source_line,
            source_line,
            dest_col,
            dest_col + self.COL_WIDTH,
        )
        if not beam_status:
            return

        if dest.is_top:
            dest_line += 1
            beam_line = source_line - 1
            beam_char = self.BEAM_CHAR_UP
        else:
            beam_line = source_line + 1
            dest_line -= 1
            beam_char = self.BEAM_CHAR_DOWN
        self.text = self._fill(
            beam_char, beam_line, dest_line, dest_col, dest_col + self.COL_WIDTH
        )

    def __str__(self):
        return self.text


class SourcePosition(str, enum.Enum):
    f"""
    "LS" laser source ports in the switchbox by their official names.

    The order of definition is intentional here: this is top-bottom sources by
    where the linear stages are as per the top-down drawings that the BTMS user
    interface utilizes.

    .. code::

        {POSITION_DIAGRAM}
    """

    ls5 = "LS5"
    ls1 = "LS1"
    ls6 = "LS6"
    ls2 = "LS2"
    ls7 = "LS7"
    ls3 = "LS3"
    ls8 = "LS8"
    ls4 = "LS4"

    @classmethod
    def from_index(cls, index: int) -> SourcePosition:
        """"
        Get a SourcePosition given its integer index.
        """
        try:
            return getattr(cls, f"ls{index}")
        except AttributeError:
            raise ValueError(f"Invalid index: {index}") from None

    @property
    def index(self) -> int:
        """"
        Get an integer index from the source position.
        """
        return int(self.name.lstrip("ls"))

    @property
    def name_and_desc(self) -> str:
        """Name and description in the form: 'LSx (desc).'"""
        return f"{self.value} ({self.description})"

    @property
    def description(self) -> str:
        """
        Description of source.

        Returns
        -------
        str
        """
        return {
            SourcePosition.ls1: "Bay 1",
            SourcePosition.ls5: "Bay 3",
            SourcePosition.ls8: "Bay 4",
        }.get(self, "Unknown")

    def is_above(self, other: SourcePosition) -> bool:
        """Is ``self`` at or above the ``other`` position?"""
        positions = list(SourcePosition)
        return positions.index(self) <= positions.index(other)

    @property
    def is_left(self) -> bool:
        """Is this laser source coming from the left (as in the diagram)?"""
        return self in (
            SourcePosition.ls1,
            SourcePosition.ls2,
            SourcePosition.ls3,
            SourcePosition.ls4,
        )

    @property
    def bay(self) -> Optional[int]:
        """The near field camera prefix associated with this source position."""
        return {
            SourcePosition.ls1: 1,
            SourcePosition.ls5: 3,
            SourcePosition.ls8: 4,
        }.get(self, None)

    @property
    def near_field_camera_prefix(self) -> Optional[str]:
        """The near field camera prefix associated with this source position."""
        bay = self.bay
        if bay is not None:
            return f"LAS:LHN:BAY{bay}:CAM:01:"
        return None

    @property
    def far_field_camera_prefix(self) -> Optional[str]:
        """The far field camera prefix associated with this source position."""
        bay = self.bay
        if bay is not None:
            return f"LAS:LHN:BAY{bay}:CAM:02:"
        return None


class DestinationPosition(str, enum.Enum):
    f"""
    "LD" laser destination ports from the switchbox.

    These are defined left-to-right as per the top-down drawings that the BTMS
    user interface utilizes.

    .. code::

        {POSITION_DIAGRAM}
    """
    # Left-right destination ports
    ld8 = "LD8"    # top
    ld1 = "LD1"    # bottom
    ld9 = "LD9"    # top
    ld2 = "LD2"    # bottom
    ld10 = "LD10"  # top
    ld3 = "LD3"    # bottom
    ld11 = "LD11"  # top
    ld4 = "LD4"    # bottom
    ld12 = "LD12"  # top
    ld5 = "LD5"    # bottom
    ld13 = "LD13"  # top
    ld6 = "LD6"    # bottom
    ld14 = "LD14"  # top
    ld7 = "LD7"    # bottom

    @property
    def name_and_desc(self) -> str:
        """Name and description in the form: 'LDx (desc).'"""
        return f"{self.value} ({self.description})"

    @property
    def description(self) -> str:
        """
        Description of destination.

        Returns
        -------
        str
        """
        return {
            DestinationPosition.ld2: "TMO IP3",
            DestinationPosition.ld4: "RIX ChemRIXS",
            DestinationPosition.ld6: "RIX QRIXS",
            DestinationPosition.ld8: "TMO IP1",
            DestinationPosition.ld9: "Laser Lab",
            DestinationPosition.ld10: "TMO IP2",
            DestinationPosition.ld14: "XPP",
        }.get(self, "Unknown")

    @classmethod
    def from_index(cls, index: int) -> DestinationPosition:
        """"
        Get a DestinationPosition given its integer index.
        """
        try:
            return getattr(cls, f"ld{index}")
        except AttributeError:
            raise ValueError(f"Invalid index: {index}") from None

    @property
    def index(self) -> int:
        """"
        Get an integer index from the source position.
        """
        return int(self.name.lstrip("ld"))

    def path_to(
        self, target: DestinationPosition
    ) -> Tuple[DestinationPosition, ...]:
        """
        Get crossed destinations on the path from ``self`` to ``target``.

        The resulting path excludes the starting position (``self``), but
        includes ``target``.

        The first ``DestinationPosition`` in the returned tuple will be the
        next closest destination.
        """
        idx1 = ALL_DESTINATIONS.index(self)
        idx2 = ALL_DESTINATIONS.index(target)

        if idx1 < idx2:
            # Direction: right (self ... target)
            return ALL_DESTINATIONS[idx1 + 1:idx2 + 1]

        # Direction: left (target ... self)
        return ALL_DESTINATIONS[idx2:idx1][::-1]

    @property
    def is_top(self) -> bool:
        """Is the laser destination a top port, as in the diagram?"""
        return self in (
            DestinationPosition.ld8,
            DestinationPosition.ld9,
            DestinationPosition.ld10,
            DestinationPosition.ld11,
            DestinationPosition.ld12,
            DestinationPosition.ld13,
            DestinationPosition.ld14,
        )


ALL_DESTINATIONS = tuple(DestinationPosition)
AnyPosition = Union[SourcePosition, DestinationPosition]


PORT_SPACING_MM = 215.9  # 8.5 in

# PV source index (bay) to installed LS port
valid_sources: Tuple[SourcePosition, ...] = (
    SourcePosition.ls1,  # Bay 1
    SourcePosition.ls5,  # Bay 3
    SourcePosition.ls8,  # Bay 4
)
# PV destination index (bay) to installed LD port
valid_destinations: Tuple[DestinationPosition, ...] = (
    DestinationPosition.ld2,   # TMO IP3
    DestinationPosition.ld4,   # RIX ChemRIXS
    DestinationPosition.ld6,   # RIX QRIXS
    DestinationPosition.ld8,   # TMO IP1
    DestinationPosition.ld9,   # Laser Lab
    DestinationPosition.ld10,  # TMO IP2
    DestinationPosition.ld14,  # XPP
)


class MoveError(Exception):
    """Cannot move according to the request."""
    ...


class PositionInvalidError(MoveError):
    """Source is not at a recognized position for BTMS to function properly."""
    #: The source that is not in a good position.
    source: SourcePosition

    def __init__(
        self,
        message: str,
        source: SourcePosition,
    ):
        super().__init__(message)
        self.source = source


class MaintenanceModeActiveError(MoveError):
    """Maintenance mode is active.  Only experts may move sources."""


class DestinationInUseError(MoveError):
    """The target destination is already in use."""
    #: The source at this destination.
    source: SourcePosition
    destination: DestinationPosition

    def __init__(
        self,
        message: str,
        source: SourcePosition,
        destination: DestinationPosition,
    ):
        super().__init__(message)
        self.source = source
        self.destination = destination


class PathCrossedError(MoveError):
    """Moving to the target destination would cross an active laser."""

    #: The active source being crossed.
    crosses_source: SourcePosition
    #: The active destination being crossed.
    crosses_destination: DestinationPosition

    def __init__(
        self,
        message: str,
        crosses_source: SourcePosition,
        crosses_destination: DestinationPosition,
    ):
        super().__init__(message)
        self.crosses_source = crosses_source
        self.crosses_destination = crosses_destination


class MovingActiveSource(MoveError):
    """The source is currently in use and should not be moved."""
    ...


class DestinationInControlError(MoveError):
    """The destination has not yielded control and does not want the source to be moved."""
    ...


@dataclasses.dataclass
class BtmsSourceState:
    """
    Per-source status.

    Attributes
    ----------
    destination : DestinationPosition (or None)
        Indicates the selected destination for the given source.
        The "target destination" is the one that the linear stage for the
        indicated source is aiming at.

    beam_status : bool
        Indicates if the beam is active for the given source.
    """
    source: SourcePosition
    destination: Optional[DestinationPosition]
    beam_status: bool


@dataclasses.dataclass
class BtmsDestinationState:
    """
    Per-destination status.

    Attributes
    ----------
    yields_control : bool
        If the destination user has acknowledged that the source it is using
        may be moved: i.e., yielding control to others.
    """
    yields_control: bool = True


@dataclasses.dataclass
class BtmsState:
    """
    Beam Transport Motion System state summary.

    Attributes
    ----------
    sources : dict of SourcePosition to BtmsSourceState
        Per-source status.
    destinations : dict of DestinationPosition to BtmsDestinationState
        Per-destination status.
    maintenance_mode : bool
        System-level maintenance mode setting.
    """
    sources: Dict[SourcePosition, BtmsSourceState] = dataclasses.field(
        default_factory=dict
    )
    destinations: Dict[DestinationPosition, BtmsDestinationState] = dataclasses.field(
        default_factory=lambda: {
            pos: BtmsDestinationState()
            for pos in DestinationPosition
        }
    )
    maintenance_mode: bool = False

    def check_configuration(self) -> List[MoveError]:
        """
        Check the current configuration for any logical errors/conflicts.
        """
        errors = []
        if self.maintenance_mode:
            errors.append(
                MaintenanceModeActiveError(
                    "Maintenance mode is active"
                )
            )

        for pos, source in self.sources.items():
            if source.destination is None:
                errors.append(
                    PositionInvalidError(
                        f"Source position is not valid {pos} ({pos.description}). "
                        f"BTMS requires that all sources be at valid destinations to "
                        f"function properly.",
                        source=pos,
                    )
                )
        return errors

    def check_move_all(
        self,
        moving_source: SourcePosition,
        closest_destination: Optional[DestinationPosition],
        target_destination: DestinationPosition,
    ) -> List[MoveError]:
        """
        Check motion of ``moving_source`` from ``closest_destination`` to
        ``target_destination``.

        Returns all conflicts along the way.

        Parameters
        ----------
        moving_source : SourcePosition
            The source to attempt to move.
        closest_destination : DestinationPosition or None
            The current destination that the source is using, or the closest
            one to it.  If None, use the position from the state.
        target_destination : DestinationPosition
            The target destination for the source to move to.

        Returns
        -------
        list of MoveError
            Any detected issues for the given move request.
        """
        errors = self.check_configuration()

        if closest_destination is None:
            closest_destination = self.sources[moving_source].destination

        dest_to_source = dict(
            (source.destination, source.source)
            for source in self.sources.values()
        )

        for other_source in self.sources:
            if other_source == moving_source:
                ...
            elif self.sources[other_source].destination == target_destination:
                errors.append(
                    DestinationInUseError(
                        f"Source {other_source} is positioned at {target_destination}",
                        source=other_source,
                        destination=target_destination,
                    )
                )

        if closest_destination is None:
            return errors

        if self.sources[moving_source].beam_status:
            dest = self.sources[moving_source].destination or "unknown"
            errors.append(
                MovingActiveSource(
                    f"{moving_source} is actively sending beam to "
                    f"{dest} and should not be moved"
                )
            )

        if closest_destination == target_destination:
            return errors

        dest = self.destinations[closest_destination]
        if not dest.yields_control:
            errors.append(
                DestinationInControlError(
                    f"{moving_source} is under the control of "
                    f"{closest_destination} ({closest_destination.description}).  "
                    f"They must yield control before the source can be moved."
                )
            )

        for dest in closest_destination.path_to(target_destination):
            active_source = dest_to_source.get(dest, None)
            if active_source is None:
                # No source is near this destination
                continue
            if not self.sources[active_source].beam_status:
                # The source is near the destination, but the beam isn't ready
                continue

            # If we're here:
            # * ``moving_source`` will move past ``dest``
            # * ``dest`` is in use with beam on
            # * We need to determine if ``moving_source`` will move through the
            #   beam or not
            dest_is_bottom = not dest.is_top
            if dest.is_top and moving_source.is_above(active_source):
                crosses_beam = True
            elif dest_is_bottom and active_source.is_above(moving_source):
                crosses_beam = True
            else:
                crosses_beam = False

            if crosses_beam:
                errors.append(
                    PathCrossedError(
                        f"Moving source {moving_source} to {target_destination} "
                        f"would cross active laser path of "
                        f"{active_source} to {dest}",
                        crosses_source=active_source,
                        crosses_destination=dest,
                    )
                )
        return errors

    def check_move(
        self,
        moving_source: SourcePosition,
        closest_destination: Optional[DestinationPosition],
        target_destination: DestinationPosition,
    ) -> None:
        """
        Check motion of ``moving_source`` from ``closest_destination`` to
        ``target_destination``.

        Parameters
        ----------
        moving_source : SourcePosition
            The source to attempt to move.
        closest_destination : DestinationPosition or None
            The current destination that the source is using, or the closest
            one to it.  If None, use the position from the state.
        target_destination : DestinationPosition
            The target destination for the source to move to.

        Raises
        ------
        MoveError
            Raises specific ``MoveError`` subclass based on the reason.
        """
        conflicts = self.check_move_all(
            moving_source, closest_destination, target_destination
        )
        # If there are any conflicts, just raise the first one for now.
        if conflicts:
            raise conflicts[0]

    def get_text_diagram(self) -> str:
        """A textual representation of the BTMS state."""
        diagram = _PositionDiagram()
        for source_pos, source in self.sources.items():
            if source.destination is not None:
                diagram.add_source(source_pos, source.destination, source.beam_status)
        return str(diagram)

    def __str__(self) -> str:
        return self.get_text_diagram()
