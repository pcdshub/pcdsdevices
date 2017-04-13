from ophyd import EpicsMotor
from .component import Component
from .iocdevice import IocDevice
from .signal import Signal


class FakeTDIR(Signal):
    """
    Fake stand-in for the missing TDIR signal.
    """
    def __init__(self, *args, **kwargs):
        self.stored_tdir = 0
        super().__init__(*args, **kwargs)

    def get(self):
        return self.stored_tdir


class IMSMotor(EpicsMotor, IocDevice):
    """
    Subclass of EpicsMotor to deal with our IOC that's missing the .TDIR field.
    The correct solution is to fix our IMS record, this is a temporary
    band-aid.
    """
    # Disable missing field that our IMS module lacks
    direction_of_travel = Component(FakeTDIR)

    def _pos_changed(self, timestamp=None, value=None, **kwargs):
        if value > self.position:
            self.direction_of_travel.stored_tdir = 1
        else:
            self.direction_of_travel.stored_tdir = 0
        super()._pos_changed(self, timestamp=timestamp, value=value, **kwargs)
