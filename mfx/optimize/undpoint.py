"""
Utilities for undulator pointing.

This may move to a library at some point
to be used in other contexts.

ACR has undulator pointing scripts that expect:
- delta_x, delta_y in microns
- "go"

There is a server-side process that ACR can start up
if we'd like to point the undulators multiple times
in a shift. This process will listen to our requests
for delta_x, delta_y, and go.

Standard procedure will be something like:
- Call ACR to set up the auto repointing
- Run one of the utilities here to either calibrate
  or realgn

The alignment is something like:
- pick a yag
- put global marker 1 on the goal position
- code calculated the centroid and finds dx, dy in pixels
- dx, dy in pixels gets converted to undulator microns
- request the move
- recalibrate? (maybe?)
"""
from lcls_tools.common.image.fit import ImageProjectionFit
from ophyd.device import Component as Cpt, FormattedComponent as FCpt, Device
from ophyd.signal import EpicsSignal, EpicsSignalRO
from ophyd.pv_positioner import PVPositioner
from pcdsdevices.signal import MultiDerivedSignal
from pcdsdevices.type_hints import SignalToValue

from .devices import YagCamera


def _get_2d_delta(mds: MultiDerivedSignal, items: SignalToValue) -> tuple[float, float]:
    return tuple(items.values())


def _put_2d_delta(mds: MultiDerivedSignal, value: tuple[float, float]) -> SignalToValue:
    return {mds.signals[0]: value[0], mds.signals[1]: value[1]}


class UndPoint2D(PVPositioner):
    """Undulator pointing variant: move by (x, y)"""
    setpoint = Cpt(
        MultiDerivedSignal,
        attrs=["delta_x", "delta_y"],
        calculate_on_get=_get_2d_delta,
        calculate_on_put=_put_2d_delta,
    )
    delta_x = Cpt(EpicsSignal, ":DELTA_X")
    delta_y = Cpt(EpicsSignal, ":DELTA_Y")
    actuate = Cpt(EpicsSignal, ":GO")
    done = FCpt(EpicsSignalRO, "{done_pvname}")

    actuate_value = 1
    done_value = 0

    def __init__(self, prefix: str, done_pvname: str, *, name: str, **kwargs):
        self.done_pvname = done_pvname
        super().__init__(prefix, name=name, **kwargs)

    def _setup_move(self, position: tuple[float, float]):
        # Also reset the actuate PV before we actuate
        self.actuate.put(1 - self.actuate_value)
        super()._setup_move(position)


class UndPoint1DX(UndPoint2D):
    """Undulator pointing variant: move in x only."""
    def _setup_move(self, position: float):
        super()._setup_move((position, 0))


class UndPoint1DY(UndPoint2D):
    """Undulator pointing variant: move in y only."""
    def _setup_move(self, position: float):
        super()._setup_move((0, position))


class UndulatorPointingRequest(Device):
    """
    Device for interfacing with the undulator repointing PVs.

    You'd use this like:

    undp = UndulatorPointingRequest("MFX:USER:MCC:UND", done_pvname="SIOC:SYS0:ML07:AO216", name="undp")
    undp.dxy.move((50, 30), wait=True)
    undp.dy.move(-100, wait=False)
    """
    dxy = FCpt(UndPoint2D, "{prefix}", done_pvname="{done_pvname}", add_prefix=("suffix", "done_pvname"))
    dx = FCpt(UndPoint1DX, "{prefix}", done_pvname="{done_pvname}", add_prefix=("suffix", "done_pvname"))
    dy = FCpt(UndPoint1DY, "{prefix}", done_pvname="{done_pvname}", add_prefix=("suffix", "done_pvname"))

    def __init__(self, prefix: str, done_pvname: str, *, name: str, **kwargs):
        self.done_pvname = done_pvname
        super().__init__(prefix, name=name, **kwargs)


class UndulatorPointingMFX(UndulatorPointingRequest):
    """
    Undulator pointing with MFX PV defaults.
    
    You can do:
    undp = UndulatorPointingMFX()
    """
    def __init__(
        self,
        prefix: str = "MFX:USER:MCC:UND",
        done_pvname: str = "SIOC:SYS0:ML07:AO216",
        *,
        name: str = "mfx_undp",
        **kwargs,
    ):
        super().__init__(prefix, name=name, done_pvname=done_pvname, **kwargs)


class UndulatorPointingMFXTest(UndulatorPointingRequest):
    """
    Use the test busy PV instead of the ACR busy PV.

    You'll need to manually flip the busy PV from 1 to 0 to signal
    that the move is done.
    """
    def __init__(
        self,
        prefix: str = "MFX:USER:MCC:UND",
        done_pvname: str = "MFX:USER:MCC:UND:TEST_BUSY",
        *,
        name: str = "test_mfx_undp",
        **kwargs,
    ):
        super().__init__(prefix, name=name, done_pvname=done_pvname, **kwargs)


def get_pixel_diff(imager: YagCamera, marker: int = 1) -> tuple[int, int]:
    """
    Return the difference in pixels between the yag's centroid and the chosen marker.

    Parameters
    ----------
    imager : YagCamera
        The imager object to use.
    marker : int
        The index of the marker to compare against.

    Returns
    -------
    pixel_diff : tuple[int, int]
        The difference in pixels between the centroid and the marker.
    """
    fit = ImageProjectionFit()
    fit_result = fit.fit_image(imager.image1.image)
    marker_pos = imager.coords.specific_marker_target(marker)
    return (
        marker_pos[0] - fit_result.centroid[0],
        marker_pos[1] - fit_result.centroid[1], 
    )
