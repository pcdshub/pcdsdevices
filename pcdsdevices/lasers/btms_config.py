from __future__ import annotations

import enum
import logging
from typing import Dict, Union

logger = logging.getLogger(__name__)


class SourcePosition(str, enum.Enum):
    # Top-bottom sources by where the linear stages are
    ls5 = "ls5"
    ls1 = "ls1"
    ls6 = "ls6"
    ls2 = "ls2"
    ls7 = "ls7"
    ls3 = "ls3"
    ls8 = "ls8"
    ls4 = "ls4"

    @property
    def is_left(self) -> bool:
        """Is the laser source coming from the left (as in the diagram)?"""
        return self in (
            SourcePosition.ls1,
            SourcePosition.ls2,
            SourcePosition.ls3,
            SourcePosition.ls4,
        )


class DestinationPosition(str, enum.Enum):
    # Left-right destination ports (top)
    ld8 = "ld8"
    ld9 = "ld9"
    ld10 = "ld10"
    ld11 = "ld11"
    ld12 = "ld12"
    ld13 = "ld13"
    ld14 = "ld14"

    # Left-right destination ports (bottom)
    ld1 = "ld1"
    ld2 = "ld2"
    ld3 = "ld3"
    ld4 = "ld4"
    ld5 = "ld5"
    ld6 = "ld6"
    ld7 = "ld7"

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


AnyPosition = Union[SourcePosition, DestinationPosition]


PORT_SPACING_MM = 215.9  # 8.5 in

# PV source index (bay) to installed LS port
source_to_ls_position: Dict[int, SourcePosition] = {
    1: SourcePosition.ls1,
    3: SourcePosition.ls5,
    4: SourcePosition.ls8,
}
# PV destination index (bay) to installed LD port
destination_to_ld_position: Dict[int, DestinationPosition] = {
    1: DestinationPosition.ld8,   # TMO IP1
    2: DestinationPosition.ld10,  # TMO IP2
    3: DestinationPosition.ld2,   # TMO IP3
    4: DestinationPosition.ld6,   # RIX QRIXS
    5: DestinationPosition.ld4,   # RIX ChemRIXS
    6: DestinationPosition.ld14,  # XPP
    7: DestinationPosition.ld9,   # Laser Lab
}


IMAGES = {
    "switchbox.png": {
        "pixels_to_mm": 1900. / 855.,
        # width: 970px - 115px = 855px is 78.0in or 1900m
        "origin": (0, 0),  # (144, 94),  # inner chamber top-left position (px)
        "positions": {
            # Sources (left side of rail, centered around axis of rotation)
            SourcePosition.ls5: (225, 138),
            SourcePosition.ls1: (225, 199),
            SourcePosition.ls6: (225, 271),
            SourcePosition.ls2: (225, 335),
            SourcePosition.ls7: (225, 402),
            SourcePosition.ls3: (225, 466),
            SourcePosition.ls8: (225, 534),
            SourcePosition.ls4: (225, 596),

            # Top destinations (rough bottom centers, inside chamber)
            DestinationPosition.ld8: (238, 94),
            DestinationPosition.ld9: (332, 94),
            DestinationPosition.ld10: (425, 94),
            DestinationPosition.ld11: (518, 94),
            DestinationPosition.ld12: (612, 94),
            DestinationPosition.ld13: (705, 94),
            DestinationPosition.ld14: (799, 94),

            # Bottom destinations (rough top centers, inside chamber)
            # Position.ld0: (191, 636),
            DestinationPosition.ld1: (285, 636),
            DestinationPosition.ld2: (379, 636),
            DestinationPosition.ld3: (473, 636),
            DestinationPosition.ld4: (567, 636),
            DestinationPosition.ld5: (661, 636),
            DestinationPosition.ld6: (752, 636),
            DestinationPosition.ld7: (842, 636),
        }
    }
}
