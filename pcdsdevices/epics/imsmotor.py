from .epicsmotor import EpicsMotor
from .component import Component
from .iocdevice import IocDevice
from .signal import (Signal, FakeSignal)

class ImsMotor(EpicsMotor, IocDevice):
    """
    Subclass of EpicsMotor to deal with our IOC that's missing the .TDIR field.
    The correct solution is to fix our IMS record, this is a temporary
    band-aid.
    """
    # Disable missing field that our IMS module lacks
    direction_of_travel = Component(FakeSignal)

    def _pos_changed(self, timestamp=None, value=None, **kwargs):
        if None not in (value, self.position):
            if value > self.position:
                self.direction_of_travel.stored_tdir = 1
            else:
                self.direction_of_travel.stored_tdir = 0
        super()._pos_changed(timestamp=timestamp, value=value, **kwargs)
