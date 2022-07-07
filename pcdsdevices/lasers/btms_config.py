from __future__ import annotations

import enum
import logging
from typing import Dict, Union

logger = logging.getLogger(__name__)


POSITION_DIAGRAM = """

             LD8   LD9  LD10  LD11  LD12  LD13  LD14
            <======================================= LS5
        LS1 =======================================>
            <======================================= LS6
        LS2 =======================================>
            <======================================= LS7
        LS3 =======================================>
            <======================================= LS8
        LS4 =======================================>
             LD1   LD2  LD3   LD4   LD5   LD6   LD7

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
    f"""
    "LD" laser destination ports from the switchbox.

    These are defined left-to-right as per the top-down drawings that the BTMS
    user interface utilizes.

    .. code::

        {POSITION_DIAGRAM}
    """
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
