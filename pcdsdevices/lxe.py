"""
'lxe' position / pulse energy pseudopositioner support.

Notes
-----
OPA::

    An optical parametric amplifier, abbreviated OPA, is a laser light source
    that emits light of variable wavelengths by an optical parametric
    amplification process. It is essentially the same as an optical parametric
    oscillator, but without the optical cavity, that is, the light beams pass
    through the apparatus just once or twice, rather than many many times.

las_comp_wp::

    Laser compressor waveplate

las_pol_wp::

    Laser polarizer waveplate

LXE::

    Laser energy motor, I assume

LXT::

    Laser x-ray timing, probably
"""

import pathlib
import time
import types
import typing

import numpy as np
from ophyd import Component as Cpt
from ophyd import EpicsSignal, PVPositioner
from scipy.constants import speed_of_light

from .device import UnrelatedComponent as UCpt
from .epics_motor import DelayNewport, EpicsMotorInterface
from .interface import FltMvInterface
from .pseudopos import (LookupTablePositioner, PseudoSingleInterface,
                        SyncAxesBase, SyncAxis, pseudo_position_argument,
                        real_position_argument)
from .signal import NotepadLinkedSignal, UnitConversionDerivedSignal
from .sim import FastMotor
from .utils import convert_unit, get_status_float, get_status_value

if typing.TYPE_CHECKING:
    import matplotlib  # noqa


def load_calibration_file(
        filename: typing.Union[pathlib.Path, str]
        ) -> np.ndarray:
    """
    Load a calibration file.

    Data will be sorted by position and need not be pre-sorted.

    Two columns of data in a space-delimited text file.  No header:
        Column 1: waveplate position [mm?]
        Column 2: pulse energy [uJ]

    Parameters
    ----------
    filename : str
        The calibration data filename.

    Returns
    -------
    np.ndarray
        Of shape (num_data_rows, 2)
    """
    data = np.loadtxt(str(filename))
    sort_indices = data[:, 0].argsort()
    return np.column_stack([data[sort_indices, 0],
                            data[sort_indices, 1]
                            ])


class LaserEnergyPlotContext:
    table: np.ndarray
    figure: 'matplotlib.figure.Figure'
    pyplot: types.ModuleType  # matplotlib.pyplot
    column_names: typing.Tuple[str, ...]
    _subplot: 'matplotlib.axes._subplots.AxesSubplot'

    def __init__(self, *,
                 table: np.ndarray,
                 column_names: typing.Sequence[str]):
        self.table = table

        # Importing forces backend selection, so do inside method
        import matplotlib.pyplot as pyplot  # noqa
        self.pyplot = pyplot
        self.figure = None
        self._subplot = None
        self.column_names = tuple(column_names)

    def close(self):
        """No longer use the existing figure, but do not close it."""
        self.figure = None

    def plot(self, new_figure=True, show=True):
        """
        Plot calibration data.

        Parameters
        ----------
        new_figure : bool, optional
            Force creation of a new figure.

        show : bool, optional
            Show the plot.
        """
        plt = self.pyplot

        if self.figure is not None:
            # New figure if the last one was closed
            new_figure = not plt.fignum_exists(self.figure.number)

        self.figure = plt.figure() if new_figure else plt.gcf()

        self._subplot = self.figure.subplots()
        self._subplot.plot(
            self.table[:, self.column_names.index('motor')],
            self.table[:, self.column_names.index('energy')],
            "k-o"
        )
        if new_figure:
            self._subplot.set_xlabel("Motor position")
            self._subplot.set_ylabel(r"Pulse energy [$\mu$J]")

        if show:
            self.figure.show()

    def add_line(self, position: float, energy: float):
        """Add a new set of lines at (position, energy)."""
        if self.figure is None:
            self.plot(show=False)

        self._subplot.axvline(position)
        self._subplot.axhline(energy)
        self.figure.canvas.draw()


class LaserEnergyPositioner(FltMvInterface, LookupTablePositioner):
    """
    Uses the lookup-table positioner to convert energy <-> motor positions.

    Uses :func:`load_calibration_file` to load the data file.

    Parameters
    ----------
    calibration_file : pathlib.Path or str
        Path to the calibration file.

    column_names : list of str, optional
        The column names.  May be omitted, assumes the first column is the
        motor position and the second column is energy.

    enable_plotting : bool, optional
        Plot each move.
    """

    _plot_context: LaserEnergyPlotContext

    energy = Cpt(PseudoSingleInterface, egu='uJ')
    motor = Cpt(EpicsMotorInterface, '')

    def __init__(self, *args,
                 calibration_file: typing.Union[pathlib.Path, str],
                 column_names: typing.Sequence[str] = None,
                 enable_plotting: bool = False,
                 **kwargs):
        table = load_calibration_file(calibration_file)
        column_names = column_names or ['motor', 'energy']
        super().__init__(*args,
                         table=table,
                         column_names=column_names,
                         **kwargs)
        self._plot_context = None
        self.enable_plotting = enable_plotting

    @property
    def enable_plotting(self) -> bool:
        return self._plot_context is not None

    @enable_plotting.setter
    def enable_plotting(self, enable: bool):
        if enable == self.enable_plotting:
            return

        if enable:
            self._plot_context = LaserEnergyPlotContext(
                table=self.table,
                column_names=self.column_names,
            )
            self._plot_context.plot()
        else:
            self._plot_context.close()
            self._plot_context = None

    @pseudo_position_argument
    def move(self, position, wait=True, timeout=None, moved_cb=None):
        ret = super().move(position, wait=wait, timeout=timeout,
                           moved_cb=moved_cb)
        if self._plot_context is not None:
            real = self.forward(position)
            self._plot_context.add_line(position=real.motor,
                                        energy=position.energy)
        return ret


class _ScaledUnitConversionDerivedSignal(UnitConversionDerivedSignal):
    UnitConversionDerivedSignal.__doc__ + """

    This semi-private class enables scaling of input/output values from
    :class:`UnitConversionDerivedSignal`.  Perhaps the only scale that will
    make sense is that of ``-1`` -- effectively reversing the direction of
    motion for a positioner.

    Attributes
    ----------
    scale : float
        The unitless scale value will be applied in both ``forward`` and
        ``inverse``: the "original" value will be multiplied by the scale,
        whereas a new user-specified setpoint value will be divided.
    """
    scale = -1

    def forward(self, value):
        '''Compute derived signal value -> original signal value'''
        if self.user_offset is not None:
            value = value - self.user_offset
        value /= self.scale
        return convert_unit(value, self.derived_units, self.original_units)

    def inverse(self, value):
        '''Compute original signal value -> derived signal value'''
        derived_value = convert_unit(value, self.original_units,
                                     self.derived_units)
        derived_value *= self.scale
        if self.user_offset is not None:
            derived_value += self.user_offset
        return derived_value


class LaserTiming(FltMvInterface, PVPositioner):
    """
    "lxt" motor, which may also have been referred to as Vitara.

    Conversions for Vitara FS_TGT_TIME nanoseconds <-> seconds are done
    internally, such that the user may work in units of seconds.
    """

    tab_component_names = True

    verbose_name = 'Laser X-ray Timing'

    _fs_tgt_time = Cpt(EpicsSignal, ':VIT:FS_TGT_TIME', auto_monitor=True,
                       kind='omitted',
                       doc='The internal nanosecond-expecting signal.'
                       )
    setpoint = Cpt(_ScaledUnitConversionDerivedSignal,
                   derived_from='_fs_tgt_time',
                   derived_units='s',
                   original_units='ns',
                   kind='hinted',
                   doc='Setpoint which handles the timing conversion.',
                   limits=(-10e-6, 10e-6),
                   )
    notepad_setpoint = Cpt(NotepadLinkedSignal, ':lxt:OphydSetpoint',
                           notepad_metadata={'record': 'ao',
                                             'default_value': 0.0},
                           kind='omitted'
                           )
    notepad_readback = Cpt(NotepadLinkedSignal, ':lxt:OphydReadback',
                           notepad_metadata={'record': 'ao',
                                             'default_value': 0.0},
                           kind='omitted'
                           )
    user_offset = Cpt(NotepadLinkedSignal, ':lxt:OphydOffset',
                      notepad_metadata={'record': 'ao', 'default_value': 0.0},
                      kind='normal',
                      doc='A Python-level user offset.'
                      )

    # A motor (record) will be moved after the above record is touched, so
    # use its done motion status:
    done = Cpt(EpicsSignal, ':MMS:PH.DMOV', auto_monitor=True, kind='omitted')
    done_value = 1

    def __init__(self, prefix='', *, egu=None, **kwargs):
        if egu not in (None, 's'):
            raise ValueError(
                f'{self.__class__.__name__} is pre-configured to work in units'
                f' of seconds.'
            )
        super().__init__(prefix, egu='s', **kwargs)

    @user_offset.sub_value
    def _offset_changed(self, value, **kwargs):
        """
        The user offset was changed.  Update the setpoint attribute.
        """
        self.setpoint.user_offset = value

    def _setup_move(self, position):
        """Update the notepad setpoint, move, and do not wait."""
        try:
            signal = self.notepad_setpoint
            if signal.connected and signal.write_access:
                if signal.get(use_monitor=True) != position:
                    signal.put(position, wait=False)
        except Exception as ex:
            self.log.debug('Failed to update notepad setpoint to position %s',
                           position, exc_info=ex)
        super()._setup_move(position)

        # Something is wrong with done signal, just sleep and pretend
        time.sleep(1)
        self._move_changed(value=1-self.done_value)
        self._move_changed(value=self.done_value)

    @done.sub_value
    def _update_position(self, old_value=None, value=None, **kwargs):
        """The move was completed. Update the notepad readback."""
        if value == self.done_value and old_value == 0:
            try:
                signal = self.notepad_readback
                position = self.setpoint.get()
                if signal.connected and signal.write_access:
                    if signal.get(use_monitor=True) != position:
                        signal.put(position, wait=False)
            except Exception as ex:
                self.log.debug('Failed to update notepad readback to position'
                               ' %s', position, exc_info=ex)

    @property
    def limits(self):
        """
        Limits as (low_limit, high_limit).

        These Python-only user limits are mirrored from `setpoint`.
        """
        return self.setpoint.limits

    @limits.setter
    def limits(self, limits):
        # Update the setpoint limits
        self.setpoint.limits = limits

    def set_current_position(self, position):
        '''
        Calculate and configure the user_offset value, indicating the provided
        ``position`` as the new current position.

        Parameters
        ----------
        position
            The new current position.
        '''
        self.user_offset.put(0.0)
        new_offset = position - self.setpoint.get()
        self.user_offset.put(new_offset)

    @property
    def dial_pos(self):
        """
        Calculate the dial position.

        The _fs_tgt_time is the actual dial_position in ns.

        Returns
        -------
        dial_pos : number
            The dial position in [s] seconds, or 'N/A' if the dial position is
            0 or None.
        """
        try:
            dial_pos = self._fs_tgt_time.get()
            # convert from ns to s
            return f'{(dial_pos * 1e-9):.3e}'
        except Exception:
            return 'N/A'

    def format_status_info(self, status_info):
        """
        Override status info handler to render the LXT motor.

        Display lxt motor status info in the ipython terminal.

        Parameters
        ----------
        status_info: dict
            Nested dictionary. Each level has keys name, kind, and is_device.
            If is_device is True, subdevice dictionaries may follow. Otherwise,
            the only other key in the dictionary will be value.

        Returns
        -------
        status: str
            Formatted string with all relevant status information.
        """
        dial_pos = self.dial_pos
        position = get_status_float(
            status_info, 'position', precision=3, format='e')
        units = get_status_value(status_info, 'setpoint', 'units')
        return f"""\
Virtual Motor {self.verbose_name} {self.prefix}
Current position (user, dial): {position} [{units}] {dial_pos} [s]
"""


class TimeToolDelay(DelayNewport):
    """
    Laser delay stage to rescale the physical time tool delay stage to units of
    time.

    A replacement for the ``txt`` motor, this class wraps the functionality of
    both the old time tool delay stage (``tt_delay``, a Newport XPS motor) and
    that of the ``DelayStage2time`` virtual motor conversions.

    The default number of bounces (2) are reused from :class:`DelayBase`.
    """


class _ReversedTimeToolDelay(DelayNewport):
    """
    An inverted version of :class:`TimeToolDelay`.
    """

    @pseudo_position_argument
    def forward(self, pseudo_pos):
        """Convert delay unit to motor unit."""
        seconds = convert_unit(-pseudo_pos.delay - self.user_offset.get(),
                               self.delay.egu, 'seconds')
        meters = seconds * speed_of_light / self.n_bounces
        motor_value = convert_unit(meters, 'meters', self.motor.egu)
        return self.RealPosition(motor=motor_value)

    @real_position_argument
    def inverse(self, real_pos):
        """Convert motor unit to delay unit."""
        meters = convert_unit(real_pos.motor, self.motor.egu, 'meters')
        seconds = meters / speed_of_light * self.n_bounces
        delay_value = convert_unit(seconds, 'seconds', self.delay.egu)
        return self.PseudoPosition(delay=-(delay_value
                                           + self.user_offset.get()))


class LaserTimingCompensation(SyncAxesBase):
    """
    LaserTimingCompensation (``lxt_ttc``) synchronously moves
    :class:`LaserTiming` (``lxt``) with :class:`TimeToolDelay` (``txt``) to
    compensate so that the true laser x-ray delay by using the ``lxt``-value
    and the result of time tool data analysis, avoiding double-counting.

    Notes
    -----
    ``delay`` and ``laser`` are intentionally renamed to non-ophyd-style
    ``txt`` and ``lxt``, respectively.
    """
    tab_component_names = True
    pseudo = Cpt(PseudoSingleInterface, limits=(-10e-6, 10e-6))
    delay = UCpt(_ReversedTimeToolDelay, doc='The **reversed** txt motor')
    laser = UCpt(LaserTiming, doc='The lxt motor')

    def __init__(self, prefix, **kwargs):
        UCpt.collect_prefixes(self, kwargs)
        super().__init__(prefix, **kwargs)
        self.delay.name = 'txt_reversed'
        self.laser.name = 'lxt'


class LxtTtcExample(SyncAxis):
    """
    Example of one way to set up the lxt_ttc construct using SyncAxis

    XPP's config on March 4, 2021
    """
    lxt = Cpt(LaserTiming, 'LAS:FS11')
    txt = Cpt(DelayNewport, 'XPP:LAS:MMN:16',
              n_bounces=14)

    tab_component_names = True
    scales = {'txt': -1}
    warn_deadband = 5e-14
    fix_sync_keep_still = 'lxt'
    sync_limits = (-10e-6, 10e-6)


class FakeLxtTtc(LxtTtcExample):
    lxt = Cpt(FastMotor)
    txt = Cpt(FastMotor)

    def __init__(self):
        super().__init__('FAKE:LXT:TTC', name='fake_lxt_ttc')
