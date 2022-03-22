from __future__ import annotations

from typing import Protocol, Union

import numpy.typing as npt

Number = Union[int, float]
PrimitiveType = Union[str, int, bool, float]

OphydBaseType = Union[
    str,
    int,
    bool,
    float,
]
OphydDataType = Union[
    OphydBaseType,
    list[OphydBaseType],
    npt.NDArray[OphydBaseType]
]


class OphydCallback(Protocol):
    def __call__(**kwargs) -> None:
        ...
