from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Dict, Optional, Tuple, Union

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


class DestinationInUseError(MoveError):
    """The target destination is already in use."""
    ...


class PathCrossedError(MoveError):
    """Moving to the target destination would cross an active laser."""
    ...


class MovingActiveSource(MoveError):
    """The source is currently in use and should not be moved."""
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
class BtmsState:
    """
    Beam Transport Motion System state summary.

    Attributes
    ----------
    positions : dict of SourcePosition to DestinationPosition (or None)
        Indicates the selected destination for the given source.
        The "target destination" is the one that the linear stage for the
        indicated source is aiming at.

    beam_status : dict of SourcePosition to bool
        Indicates if the beam is active for the given source.
    """
    sources: Dict[SourcePosition, BtmsSourceState] = dataclasses.field(
        default_factory=dict
    )

    def check_configuration(self) -> None:
        """Check the current configuration for any logical errors."""
        # TODO: anything important to check here?

    def check_move(
        self,
        moving_source: SourcePosition,
        closest_destination: DestinationPosition,
        target_destination: DestinationPosition,
    ) -> None:
        """
        Check motion of ``moving_source`` from ``closest_destination`` to
        ``target_destination``.

        Parameters
        ----------
        moving_source : SourcePosition
            The source to attempt to move.
        closest_destination : DestinationPosition
            The current destination that the source is using, or the closest
            one to it.
        target_destination : DestinationPosition
            The target destination for the source to move to.

        Raises
        ------
        MoveError
            Raises specific ``MoveError`` subclass based on the reason.
        """
        self.check_configuration()

        dest_to_source = dict(
            (source.destination, source.source)
            for source in self.sources.values()
        )

        if self.sources[moving_source].beam_status:
            raise MovingActiveSource(
                f"{moving_source} is active and should not be moved"
            )

        if self.sources[moving_source].destination == target_destination:
            return

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
                raise PathCrossedError(
                    f"Moving source {moving_source} to {target_destination} "
                    f"would cross active laser path of "
                    f"{active_source} to {dest}"
                )
