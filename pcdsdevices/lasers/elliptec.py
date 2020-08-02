"""
Classes for ThorLabs Elliptec motors.
"""


from ophyd import FormattedComponent as FCpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO


class EllBase(Device):
    """
    Base class for Elliptec stages.

    Sufficient for control of ELL17/20 (28/60mm linear stages) and ELL14/18
    (rotation) stages.

    Parameters
    ----------
    prefix : str
        The PV base of the stage.
    channel : str 
        The motor channel on the controller (0-E)
    port : str
        The port of the Elliptec controller (typically 0)
    """
    set_position = FCpt(EpicsSignal, '{prefix}:M{self._channel}:CURPOS',
                        write_pv='{prefix}:M{self._channel}:MOVE',
                        kind='normal')
    status = FCpt(EpicsSignalRO, '{prefix}:M{self._channel}:STATUS',
                  kind='normal')
    _from_addr = FCpt(EpicsSignal, '{prefix}:PORT{self._port}:FROM_ADDR',
                      kind='omitted')
    _to_addr = FCpt(EpicsSignal, '{prefix}:PORT{self._port}:TO_ADDR',
                    kind='omitted')
    _save_addr = FCpt(EpicsSignal, '{prefix}:PORT{self._port}:SAVE',
                      kind='omitted')
    _command = FCpt(EpicsSignal, '{prefix}:PORT{self._port}:CMD',
                    kind='omitted')
    _response = FCpt(EpicsSignalRO, '{prefix}:PORT{self._port}:RESPONSE',
                     kind='omitted')

    def __init__(self, prefix, port=0, channel=1, **kwargs):
        self._port = port
        self._channel=channel
        super().__init__(prefix, **kwargs)

class Ell6(EllBase):
    """
    Class for Thorlabs ELL6 2 position filter slider.
    """

    # Names for slider positions
    name_0 = FCpt(EpicsSignal, '{prefix}:M{self._channel}:NAME0',
                  kind='config')
    name_1 = FCpt(EpicsSignal, '{prefix}:M{self._channel}:NAME1',
                  kind='config')


class Ell9(Ell6):
    """
    Class for Thorlabs ELL9 4 position filter slider.
    """

    # Names for slider positions
    name_2 = FCpt(EpicsSignal, '{prefix}:M{self._channel}:NAME2',
                  kind='config')
    name_3 = FCpt(EpicsSignal, '{prefix}:M{self._channel}:NAME3',
                  kind='config')


class EllLinear(EllBase):
    """
    Class for Thorlabs ELL17/20 (28/60mm) linear stage.
    """
    _current_precision = FCpt(EpicsSignal,
                              '{prefix}:M{self._channel}:CURPOS.PREC',
                              kind='omitted')
    _current_egu = FCpt(EpicsSignal, '{prefix}:M{self._channel}:CURPOS.EGU',
                        kind='omitted')
    _target_precision = FCpt(EpicsSignal,
                             '{prefix}:M{self._channel}:MOVE.PREC',
                             kind='omitted')
    _target_egu = FCpt(EpicsSignal, '{prefix}:M{self._channel}:MOVE.EGU',
                       kind='omitted')

 
class EllRotation(EllLinear):
    """
    Class for Thorlabs ELL14/18 (rotation) stages.
    """
