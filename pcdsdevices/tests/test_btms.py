from typing import Optional, Tuple

import pytest

from ..lasers.btms_config import (BtmsState, DestinationPosition,
                                  MovingActiveSource, PathCrossedError,
                                  SourcePosition)


@pytest.mark.parametrize(
    "dest1, dest2, path",
    [
        pytest.param(
            DestinationPosition.ld8,
            DestinationPosition.ld10,
            (
                DestinationPosition.ld1,
                DestinationPosition.ld9,
                DestinationPosition.ld2,
                DestinationPosition.ld10,
            ),
        ),
        pytest.param(
            DestinationPosition.ld10,
            DestinationPosition.ld8,
            (
                DestinationPosition.ld2,
                DestinationPosition.ld9,
                DestinationPosition.ld1,
                DestinationPosition.ld8,
            ),
        ),
        pytest.param(
            DestinationPosition.ld8,
            DestinationPosition.ld8,
            (),
        ),
        pytest.param(
            DestinationPosition.ld14,
            DestinationPosition.ld7,
            (DestinationPosition.ld7,),
        ),
    ],
)
def test_destination_position_path(
    dest1: DestinationPosition,
    dest2: DestinationPosition,
    path: Tuple[DestinationPosition, ...],
):
    assert dest1.path_to(dest2) == path


@pytest.mark.parametrize(
    "dest, top",
    [
        (DestinationPosition.ld8, True),
        (DestinationPosition.ld9, True),
        (DestinationPosition.ld10, True),
        (DestinationPosition.ld11, True),
        (DestinationPosition.ld12, True),
        (DestinationPosition.ld13, True),
        (DestinationPosition.ld14, True),
        (DestinationPosition.ld1, False),
        (DestinationPosition.ld2, False),
        (DestinationPosition.ld3, False),
        (DestinationPosition.ld4, False),
        (DestinationPosition.ld5, False),
        (DestinationPosition.ld6, False),
        (DestinationPosition.ld7, False),
    ],
)
def test_destination_is_top(dest: DestinationPosition, top: bool):
    assert dest.is_top is top


@pytest.mark.parametrize(
    "source1, source2, above",
    [
        (SourcePosition.ls5, SourcePosition.ls1, True),
        (SourcePosition.ls1, SourcePosition.ls5, False),
        (SourcePosition.ls5, SourcePosition.ls8, True),
        (SourcePosition.ls4, SourcePosition.ls5, False),
        (SourcePosition.ls2, SourcePosition.ls8, True),
    ],
)
def test_source_position_path(
    source1: SourcePosition,
    source2: SourcePosition,
    above: bool
):
    assert source1.is_above(source2) is above


@pytest.mark.parametrize(
    "source, start, end, expected",
    [
        pytest.param(
            SourcePosition.ls3,
            DestinationPosition.ld7,
            DestinationPosition.ld8,
            None,
            id="ls3_can_move_freely_left",
        ),
        pytest.param(
            SourcePosition.ls3,
            DestinationPosition.ld8,
            DestinationPosition.ld7,
            None,
            id="ls3_can_move_freely_right",
        ),
        pytest.param(
            SourcePosition.ls3,
            DestinationPosition.ld8,
            DestinationPosition.ld7,
            None,
            id="ls3_can_move_freely_right",
        ),
        pytest.param(
            SourcePosition.ls6,
            DestinationPosition.ld9,
            DestinationPosition.ld10,
            MovingActiveSource("is active"),
            id="ls6_is_active",
        ),
        pytest.param(
            SourcePosition.ls2,
            DestinationPosition.ld13,
            DestinationPosition.ld8,
            None,
            id="ls2_can_move_freely_left",
        ),
        pytest.param(
            SourcePosition.ls2,
            DestinationPosition.ld8,
            DestinationPosition.ld10,
            None,
            id="ls2_move_past_ld9_ok",
        ),
        pytest.param(
            SourcePosition.ls2,
            DestinationPosition.ld8,
            DestinationPosition.ld7,
            PathCrossedError("LS7 to LD14"),
            id="ls2_move_past_ld14_bad",
        ),
    ],
)
def test_move_scenario_1(
    source: SourcePosition,
    start: DestinationPosition,
    end: DestinationPosition,
    expected: Optional[Exception],
):
    # Scenario 1:
    #        LD8   LD9  LD10  LD11  LD12  LD13  LD14
    #       <======^^^==========================^^^=== LS5
    #   LS1 =======^^^==========================^^^==>
    #       <======|||==========================^^^=== LS6
    #   LS2 ====================================^^^==>
    #       <===================================|||=== LS7
    #   LS3 =========================================>
    #       <========================================= LS8
    #   LS4 =========================================>
    #          LD1   LD2    LD3  LD4   LD5   LD6   LD7

    state = BtmsState(
        positions={
            SourcePosition.ls6: DestinationPosition.ld9,
            SourcePosition.ls7: DestinationPosition.ld14,
        },
        beam_status={
            SourcePosition.ls6: True,
            SourcePosition.ls7: True,
        }
    )

    if source not in state.positions:
        state.positions[source] = None
        state.beam_status[source] = False

    if expected is not None:
        with pytest.raises(type(expected), match=str(expected)):
            state.check_move(source, start, end)
    else:
        state.check_move(source, start, end)


@pytest.mark.parametrize(
    "source, left_hits, right_hits",
    [
        pytest.param(
            SourcePosition.ls5,
            SourcePosition.ls6,  # move left to conflict with LS6
            SourcePosition.ls4,  # move left to conflict with LS4
        ),
        pytest.param(
            SourcePosition.ls1,
            SourcePosition.ls6,
            SourcePosition.ls4,
        ),
        pytest.param(
            SourcePosition.ls2,
            None,
            SourcePosition.ls4,
        ),
        pytest.param(
            SourcePosition.ls7,
            None,
            SourcePosition.ls4,
        ),
        pytest.param(
            SourcePosition.ls8,
            SourcePosition.ls3,
            SourcePosition.ls4,
        ),
    ],
)
def test_move_scenario_2(
    source: SourcePosition,
    left_hits: Optional[SourcePosition],
    right_hits: SourcePosition,
):
    # Scenario 2:
    #        LD8   LD9  LD10  LD11  LD12  LD13  LD14
    #       <======^^^===========|||======^^^========= LS5
    #   LS1 =======^^^===========|||======^^^========>
    #       <======|||====================^^^========= LS6
    #   LS2 =====================|||======^^^========>
    #       <====================|||======^^^========= LS7
    #   LS3 ================|||===========^^^========>
    #       <===============...==|||======^^^========= LS8
    #   LS4 ================...===========|||========>
    #          LD1   LD2    LD3  LD4   LD5   LD6   LD7

    state = BtmsState(
        positions={
            SourcePosition.ls1: DestinationPosition.ld4,
            SourcePosition.ls2: DestinationPosition.ld4,
            SourcePosition.ls3: DestinationPosition.ld3,
            SourcePosition.ls4: DestinationPosition.ld13,
            SourcePosition.ls5: DestinationPosition.ld4,
            SourcePosition.ls6: DestinationPosition.ld9,
            SourcePosition.ls7: DestinationPosition.ld4,
            SourcePosition.ls8: DestinationPosition.ld4,
        },
        beam_status={
            SourcePosition.ls1: False,
            SourcePosition.ls2: False,
            SourcePosition.ls3: True,
            SourcePosition.ls4: True,
            SourcePosition.ls5: False,
            SourcePosition.ls6: True,
            SourcePosition.ls7: False,
            SourcePosition.ls8: False,
        }
    )

    start_pos = state.positions[source]
    assert start_pos is not None

    # Move all the way left:
    if left_hits is None:
        # Should be able to move there just fine
        state.check_move(source, start_pos, DestinationPosition.ld8)
    else:
        # Expect to hit into "left_hits"
        with pytest.raises(PathCrossedError, match=left_hits.value):
            state.check_move(source, start_pos, DestinationPosition.ld8)

    # Move all the way right - expect to hit into "right_hits"
    with pytest.raises(PathCrossedError, match=right_hits.value):
        state.check_move(source, start_pos, DestinationPosition.ld7)
