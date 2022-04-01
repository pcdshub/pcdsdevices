from __future__ import annotations

from typing import Dict, Optional, Protocol, Union, runtime_checkable

import numpy.typing as npt
import ophyd

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


SignalToValue = Dict[ophyd.Signal, OphydDataType]


@runtime_checkable
class MdsOnGetFunction(Protocol):
    """Calculation handler for MultiDerivedSignal."""
    def __call__(
        self, mds: ophyd.Signal, items: SignalToValue
    ) -> OphydDataType:
        ...


@runtime_checkable
class MdsOnPutFunction(Protocol):
    """Put handler for MultiDerivedSignal."""
    def __call__(
        self, mds: ophyd.Signal, value: OphydDataType
    ) -> Optional[SignalToValue]:
        ...
