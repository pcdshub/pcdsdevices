"""
Classes for ThorLabs Elliptec motors.
"""


from ophyd import FormattedComponent as FCpt
from ophyd import Device
from ophyd.signal import EpicsSignal, EpicsSignalRO
from pcdsdevices.variety import set_metadata


class EllBase(Device):
    """
    Base class for Elliptec stages.
    """
    set_position = FCpt(EpicsSignal, '{prefix}:M{self._channel}:CURPOS',
                        write_pv='{prefix}:M{self._channel}:MOVE',
                        kind='normal')

    jog_fwd = FCpt(EpicsSignal, '{prefix}:M{self._channel}:MOVE_FWD',
                   kind='normal')
    set_metadata(jog_fwd, dict(variety='command-proc', value=1))

    jog_bwd = FCpt(EpicsSignal, '{prefix}:M{self._channel}:MOVE_BWD',
                   kind='normal')
    set_metadata(jog_bwd, dict(variety='command-proc', value=1))

    status = FCpt(EpicsSignalRO, '{prefix}:M{self._channel}:STATUS',
                  kind='normal')

    optimize = FCpt(EpicsSignal, '{prefix}:M{self._channel}:OPTIMIZE',
                    kind='omitted')
    set_metadata(optimize, dict(variety='command-proc', value=1))

    _from_addr = FCpt(EpicsSignal, '{prefix}:PORT{self._port}:FROM_ADDR',
                      kind='omitted')
    _to_addr = FCpt(EpicsSignal, '{prefix}:PORT{self._port}:TO_ADDR',
                    kind='omitted')
    _save = FCpt(EpicsSignal, '{prefix}:PORT{self._port}:SAVE',
                 kind='omitted')
    _command = FCpt(EpicsSignal, '{prefix}:PORT{self._port}:CMD',
                    kind='omitted')
    _response = FCpt(EpicsSignalRO, '{prefix}:PORT{self._port}:RESPONSE',
                     kind='omitted')

    def __init__(self, prefix, port=0, channel=1, **kwargs):
        self._port = port
        self._channel = channel
        super().__init__(prefix, **kwargs)


class Ell6(EllBase):
    """
    Class for Thorlabs ELL6 2 position filter slider.

    Parameters
    ----------
    prefix : str
        The PV base of the stage.
    channel : str
        The motor channel on the controller (0-F)
    port : str
        The port of the Elliptec controller (typically 0)

    Examples
    --------
    ell6 = Ell6('LM1K4:COM_DP1_TF1_SL1:ELL', port=0, channel=1, name='ell6')
    """
    # Names for slider positions
    name_0 = FCpt(EpicsSignal, '{prefix}:M{self._channel}:NAME0',
                  kind='config')
    name_1 = FCpt(EpicsSignal, '{prefix}:M{self._channel}:NAME1',
                  kind='config')


class Ell9(Ell6):
    """
    Class for Thorlabs ELL9 4 position filter slider.

    Parameters
    ----------
    prefix : str
        The PV base of the stage.
    channel : str
        The motor channel on the controller (0-F)
    port : str
        The port of the Elliptec controller (typically 0)

    Examples
    --------
    ell9 = Ell9('LM1K4:COM_DP1_TF1_SL1:ELL', port=0, channel=1, name='ell9')
    """
    home = FCpt(EpicsSignal, '{prefix}:M{self._channel}:HOME',
                kind='config')
    set_metadata(home, dict(variety='command-proc', value=1))

    # Names for slider positions
    name_2 = FCpt(EpicsSignal, '{prefix}:M{self._channel}:NAME2',
                  kind='config')
    name_3 = FCpt(EpicsSignal, '{prefix}:M{self._channel}:NAME3',
                  kind='config')


class EllLinear(EllBase):
    """
    Class for Thorlabs ELL17/20 (28/60mm) linear stage.

    Parameters
    ----------
    prefix : str
        The PV base of the stage.
    channel : str
        The motor channel on the controller (0-F)
    port : str
        The port of the Elliptec controller (typically 0)

    Examples
    --------
    ell17 = EllLinear('LM1K4:COM_DP1_TF1_LIN1:ELL', port=0, channel=1,
                       name='ell17')
    """
    home = FCpt(EpicsSignal, '{prefix}:M{self._channel}:HOME',
                kind='config')
    set_metadata(home, dict(variety='command-proc', value=1))

    jog_step = FCpt(EpicsSignal, '{prefix}:M{self._channel}:GET_JOG',
                    write_pv='{prefix}:M{self._channel}:SET_JOG',
                    kind='config')

    clean = FCpt(EpicsSignal, '{prefix}:M{self._channel}:CLEAN_MECH',
                 kind='omitted')
    set_metadata(clean, dict(variety='command-proc', value=1))

    stop_optimize = FCpt(EpicsSignal, '{prefix}:M{self._channel}:STOP',
                         kind='omitted')
    set_metadata(stop_optimize, dict(variety='command-proc', value=1))

    current_egu = FCpt(EpicsSignal, '{prefix}:M{self._channel}:CURPOS.EGU',
                       kind='omitted')
    target_egu = FCpt(EpicsSignal, '{prefix}:M{self._channel}:MOVE.EGU',
                      kind='omitted')


class EllRotation(EllLinear):
    """
    Class for Thorlabs ELL14/18 (rotation) stages.

    Parameters
    ----------
    prefix : str
        The PV base of the stage.
    channel : str
        The motor channel on the controller (0-F)
    port : str
        The port of the Elliptec controller (typically 0)

    Examples
    --------
    ell14 = EllRotation('LM1K4:COM_DP1_TF1_ROT1:ELL', port=0, channel=1,
                         name='ell14')
    """
    # Currently no difference between rotation implementation and linear
    # implementation, but there may be eventually, and I couldn't come up with
    # a good name to encapsulate them both.
