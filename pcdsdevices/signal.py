"""
Module to define ophyd Signal subclass utilities.
"""
# Catch semi-frequent issue with scripts accidentally run from inside module
if __name__ != 'pcdsdevices.signal':
    raise RuntimeError('A script tried to import pcdsdevices.signal '
                       'instead of the signal built-in module. This '
                       'usually happens when a script is run from '
                       'inside the pcdsdevices directory and can cause '
                       'extremely confusing bugs. Please run your script '
                       'elsewhere for better results.')
import contextlib
import dataclasses
import inspect
import itertools
import logging
import numbers
import typing
from threading import RLock
from typing import Any, Dict, Generator, List, Mapping, Optional, Tuple, Union

import numpy as np
import ophyd
from ophyd.signal import (DEFAULT_WRITE_TIMEOUT, DerivedSignal, EpicsSignal,
                          EpicsSignalBase, EpicsSignalRO, Signal, SignalRO)
from ophyd.sim import FakeEpicsSignal, FakeEpicsSignalRO, fake_device_cache
from ophyd.utils import ReadOnlyError
from pytmc.pragmas import normalize_io

from . import utils
from .type_hints import (MdsOnGetFunction, MdsOnPutFunction, Number,
                         OphydCallback, OphydDataType)
from .utils import convert_unit

logger = logging.getLogger(__name__)


class PytmcSignal(EpicsSignalBase):
    """
    Class for a connection to a pytmc-generated EPICS record.

    This uses the same args as the pragma, so you can refer to the pytmc
    pragmas to select args for your components. This will automatically append
    the '_RBV' suffix and wrap the read/write PVs into the same signal object
    as appropriate, and pick between a read-only signal and a writable one.

    Under the hood this actually gives you the RW or RO version of the signal
    depending on your io argument.
    """

    def __new__(cls, prefix, io=None, **kwargs):
        new_cls = select_pytmc_class(io=io, prefix=prefix,
                                     write_cls=PytmcSignalRW,
                                     read_only_cls=PytmcSignalRO)
        return super().__new__(new_cls)

    def __init__(self, prefix, *, io, **kwargs):
        self.pytmc_pv = prefix
        self.pytmc_io = io
        super().__init__(prefix + '_RBV', **kwargs)


def select_pytmc_class(io=None, *, prefix, write_cls, read_only_cls):
    """Return the class to use for PytmcSignal's constructor."""
    if io is None:
        # Provide a better error here than "__new__ missing an arg"
        raise ValueError('Must provide an "io" argument to PytmcSignal. '
                         f'This is missing for signal with pv {prefix}. '
                         'Feel free to copy the io field from the '
                         'pytmc pragma.')
    if pytmc_writable(io):
        return write_cls
    else:
        return read_only_cls


def pytmc_writable(io):
    """Returns `True` if the pytmc io arg represents a writable PV."""
    norm = normalize_io(io)
    if norm == 'output':
        return True
    elif norm == 'input':
        return False
    else:
        # Should never get here unless pytmc's API changes
        raise ValueError(f'Invalid io specifier {io}')


class PytmcSignalRW(PytmcSignal, EpicsSignal):
    """Read-write connection to a pytmc-generated EPICS record."""
    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, write_pv=prefix, **kwargs)


class PytmcSignalRO(PytmcSignal, EpicsSignalRO):
    """Read-only connection to a pytmc-generated EPICS record."""
    pass


# Make sure an acceptable fake class is set for PytmcSignal
class FakePytmcSignal(FakeEpicsSignal):
    """A suitable fake class for PytmcSignal."""
    def __new__(cls, prefix, io=None, **kwargs):
        new_cls = select_pytmc_class(io=io, prefix=prefix,
                                     write_cls=FakePytmcSignalRW,
                                     read_only_cls=FakePytmcSignalRO)
        return super().__new__(new_cls)

    def __init__(self, prefix, io=None, **kwargs):
        super().__init__(prefix + '_RBV', **kwargs)


class FakePytmcSignalRW(FakePytmcSignal, FakeEpicsSignal):
    def __init__(self, prefix, **kwargs):
        super().__init__(prefix, write_pv=prefix, **kwargs)


class FakePytmcSignalRO(FakePytmcSignal, FakeEpicsSignalRO):
    pass


# NOTE: This is an *on-import* update of the ophyd "fake" device cache
fake_device_cache[PytmcSignal] = FakePytmcSignal


@dataclasses.dataclass
class _AggregateSignalState:
    """
    This class holds per-Signal state information when used as part of an
    AggregateSignal.

    It includes a cache of the last value, connectivity status, and callback
    identifiers from ophyd.
    """
    #: The signal itself
    signal: Signal
    #: Is the signal connected according to its metadata callback?
    connected: bool = False
    #: The last value retrieved from a value callback, or a direct get request.
    value: Optional[OphydDataType] = None
    #: The value subscription callback ID (None if not yet subscribed)
    value_cbid: Optional[int] = None
    #: The meta subscription callback ID (None if not yet subscribed)
    meta_cbid: Optional[int] = None


class AggregateSignal(Signal):
    """
    Signal that is composed of a number of other signals.

    This class exists to handle the group subscriptions without repeatedly
    getting the values of all the subsignals at all times.

    This signal type is intended to be used programmatically with a subclass.
    For simple per-device usage, see :class:`MultiDerivedSignal`.
    """

    _update_only_on_change: bool = True
    _has_subscribed: bool
    _signals: Dict[Signal, _AggregateSignalState]

    def __init__(self, *, name, value=None, **kwargs):
        super().__init__(name=name, value=value, **kwargs)
        self._has_subscribed = False
        self._lock = RLock()
        self._signals = {}

    def _calc_readback(self):
        """
        Override this with a calculation to find the current state given the
        cached values.

        Returns
        -------
        readback
            The result of the calculation.
        """

        raise NotImplementedError(
            'Subclasses must implement _calc_readback'
        )  # pragma nocover

    def _insert_value(self, signal, value):
        """Update the cache with one value and recalculate."""
        with self._lock:
            self._signals[signal].value = value
            self._update_readback()
            return self._readback

    @property
    def _have_values(self) -> bool:
        """Is the value cache populated?"""
        return all(
            siginfo.value is not None for siginfo in self._signals.values()
        )

    def _update_readback(self) -> Optional[OphydDataType]:
        """
        Recalculate the readback value.

        Requires that the signal info cache has been updated prior to the
        call.  This information could be sourced via subscriptions or manually
        queried updates as in ``.get()``.

        Returns
        -------
        value : OphydDataType or None
            This is the newly-calculated value, if available. If there are
            missing values in the cache, the previously-calculated readback
            value (or the default passed into the ``Signal`` instance or
            ``None``) will be returned.
        """
        with self._lock:
            if self._have_values:
                self._readback = self._calc_readback()
            return self._readback

    def get(self, **kwargs):
        """
        Update all values and recalculate.

        Parameters
        ----------
        **kwargs :
            Keyword arguments are passed to each ``signal.get(**kwargs)``.
        """
        with self._lock:
            for signal, siginfo in self._signals.items():
                siginfo.value = signal.get(**kwargs)
            return self._update_readback()

    def put(self, value, **kwargs):
        raise NotImplementedError(
            'put should be overridden in a subclass'
        )  # pragma nocover

    def subscribe(self, cb, event_type=None, run=True):
        cid = super().subscribe(cb, event_type=event_type, run=run)
        recognized_event = event_type in (None, self.SUB_VALUE, self.SUB_META)
        if recognized_event and not self._has_subscribed:
            self._setup_subscriptions()

        return cid

    subscribe.__doc__ = ophyd.ophydobj.OphydObject.subscribe.__doc__

    def _setup_subscriptions(self):
        """Subscribe to all relevant signals."""
        with self._lock:
            if self._has_subscribed:
                return

            self._has_subscribed = True

        try:
            for signal, siginfo in self._signals.items():
                self.log.debug("Subscribing %s", signal.name)
                if siginfo.value_cbid is not None:
                    # Only subscribe once.
                    continue

                siginfo.meta_cbid = signal.subscribe(
                    self._signal_meta_callback,
                    run=True,
                    event_type=signal.SUB_META,
                )
                siginfo.value_cbid = signal.subscribe(
                    self._signal_value_callback,
                    run=True,
                )
        except Exception:
            self.log.exception("Failed to subscribe to signals")

    def wait_for_connection(self, *args, **kwargs):
        """Wait for underlying signals to connect."""
        self._setup_subscriptions()
        return super().wait_for_connection(*args, **kwargs)

    def _signal_meta_callback(
        self, *, connected: bool = False, obj: Signal, **kwargs
    ) -> None:
        """This is a SUB_META callback from one of the aggregated signals."""
        with self._check_connectivity():
            self._signals[obj].connected = connected

    def _signal_value_callback(self, *, obj: Signal, **kwargs):
        """This is a SUB_VALUE callback from one of the aggregated signals."""
        kwargs.pop('sub_type')
        kwargs.pop('old_value')
        value = kwargs['value']
        with self._lock:
            old_value = self._readback
            # Update just one value and assume the rest are cached
            # This allows us to run subs without EPICS gets
            # Run metadata callbacks before the value callback, if appropriate
            with self._check_connectivity() as connectivity_info:
                value = self._insert_value(obj, value)
            if connectivity_info["sent_value_callback"]:
                # Avoid sending a duplicate SUB_VALUE event since the
                # connectivity check above did it already
                return
            if value != old_value or not self._update_only_on_change:
                self._run_subs(sub_type=self.SUB_VALUE, obj=self, value=value,
                               old_value=old_value)

    @property
    def connected(self) -> bool:
        """Are all relevant signals connected?"""
        if self._destroyed:
            return False

        if self._has_subscribed:
            return all(
                siginfo.connected and siginfo.value is not None
                for siginfo in self._signals.values()
            )

        # Only check connectivity status of the signal; cross fingers that it
        # reflects both being connected and having a not-None value.
        return all(signal.connected for signal in self._signals)

    @contextlib.contextmanager
    def _check_connectivity(self) -> Generator[Dict[str, bool], None, None]:
        """
        Context manager for checking connectivity.

        The block for the context manager should perform some operation
        to change the state of the signal.

        Returns state information as a dictionary, accessible after the
        context manager block has finished evaluation.
        """
        was_connected = self.connected
        state_info = {
            "was_connected": was_connected,
            "is_connected": was_connected,
            "sent_md_callback": False,
            "sent_value_callback": False,
        }

        yield state_info

        # Now that the caller has updated state, check to see if our
        # connectivity status has changed.  Update the mutable return
        # value at this point.
        is_connected = self.connected
        state_info["is_connected"] = is_connected
        if was_connected != is_connected:
            self._metadata["connected"] = is_connected
            self._run_metadata_callbacks()
            state_info["sent_md_callback"] = True

        if not was_connected and is_connected:
            # disconnected -> connected; give a proper value callback.
            # "connected" indicates that:
            # 1. All underlying signals are connected
            # 2. All underlying signals have a value cached
            with self._lock:
                old_value = self._readback
                self._readback = self._calc_readback()
                self._run_subs(
                    sub_type=self.SUB_VALUE,
                    obj=self,
                    value=self._readback,
                    old_value=old_value,
                )
                state_info["sent_value_callback"] = True

    def add_signal_by_attr_name(self, name: str) -> Signal:
        """
        Add a signal from which to aggregate information.

        This must be called before any subscriptions are made to the signal.
        Duplicate signals will not be re-added.

        Parameters
        ----------
        name : str
            The attribute name of the signal, relative to the parent device.

        Returns
        -------
        sig : ophyd.Signal
            The signal referenced by the attribute name.

        Raises
        ------
        RuntimError
            If called after .subscribe() or used without a parent Device.
        """
        if self._has_subscribed:
            raise RuntimeError(
                "Cannot add signals to an AggregateSignal after it has been "
                "subscribed to."
            )

        sig = self.parent

        if sig is None:
            raise RuntimeError(
                "Cannot use an AggregateSignal with attribute names outside "
                "of a Device/Component hierarchy."
            )

        for part in name.split('.'):
            sig = getattr(sig, part)

        # Add if not yet there; but do not subscribe just yet.
        self._signals[sig] = _AggregateSignalState(signal=sig)
        return sig

    def destroy(self):
        for signal, info in self._signals.items():
            if info.value_cbid is not None:
                signal.unsubscribe(info.value_cbid)
                info.value_cbid = None

            if info.meta_cbid is not None:
                signal.unsubscribe(info.meta_cbid)
                info.meta_cbid = None

        return super().destroy()


class SummarySignal(AggregateSignal):
    """
    Signal that holds a hash of the values of the constituent signals.

    Meant to allow tracking of constituent signals via callbacks.

    The calculated readback value is useless, and should not be used
    in any downstream calculations.  Use the signal/PV you actually
    care about instead.
    """
    def _calc_readback(self):
        values = tuple(sig.get() for sig in self._signals)
        # We return a hash here, rather than the tuple, to always provide
        # an ophyd-compatible datatype.
        return hash(values)


class PVStateSignal(AggregateSignal):
    """
    Signal that implements the `PVStatePositioner` state logic.

    See `AggregateSignal` for more information.
    """
    _metadata_keys = Signal._core_metadata_keys + (
        'enum_strs',
    )

    def __init__(self, *, name, **kwargs):
        super().__init__(name=name, **kwargs)
        for attr_name in self.parent._state_logic:
            self.add_signal_by_attr_name(attr_name)
        self._has_setpoint_md = False

    @property
    def enum_strs(self) -> Tuple[str, ...]:
        """
        Mimic the epics signal property for enum strings.
        """
        return tuple(state.name for state in self.parent.states_enum)

    def describe(self) -> Dict[str, Dict[str, Any]]:
        """
        Make sure a reasonable description exists for bluesky scans.
        """
        # Base description information
        sub_sigs = [sig.name for sig in self._signals]
        desc = {
            'source': 'SUM:{}'.format(','.join(sub_sigs)),
            'dtype': 'string',
            'shape': [],
            'enum_strs': self.enum_strs,
        }
        return {self.name: desc}

    def _calc_readback(self) -> str:
        """
        Implements the PVStatePositioner logic.

        This relies on this signal being a component of a PVStatePositioner
        class with properly-defined class attributes.

        On the first call, we'll do some setup of metadata values, since
        this first call happens after the signals connect and we're guaranteed
        that everything is ready. Doing it earlier can run into some
        race conditions.
        """
        # Do some one-time setup here
        # Convenient because we only hit this block when signals are ready
        if (
            self._metadata['enum_strs'] is None
            and self.parent._state_initialized
        ):
            # One time setup of the enum strs
            # Defined by class definition, not by EPICS
            # Not necessarily available during init though, so do it now
            self._metadata['enum_strs'] = self.enum_strs
            self._run_metadata_callbacks()
        if not self._has_setpoint_md:
            # One time setup of the setpoint signal's metadata
            # We need this to apply e.g. write permissions
            ref_str = self.parent._state_logic_set_ref
            if isinstance(ref_str, str):
                setpoint_sig = getattr(self.parent, ref_str)
                setpoint_sig.subscribe(
                    self._setpoint_md_update,
                    setpoint_sig.SUB_META,
                )
            self._has_setpoint_md = True

        state_value = None
        for states, sig_info in zip(
            self.parent._state_logic.values(), self._signals.values()
        ):
            # Get state information from last cached value
            try:
                signal_state = states[sig_info.value]
            # Handle unaccounted readbacks
            except KeyError:
                state_value = self.parent._unknown
                break
            # Associate readback with device state
            if signal_state != 'defer':
                if state_value:
                    # Handle inconsistent readbacks
                    if signal_state != state_value:
                        state_value = self.parent._unknown
                        break
                else:
                    # Set state to first non-deferred value
                    state_value = signal_state
                    if self.parent._state_logic_mode == 'ALL':
                        continue
                    elif self.parent._state_logic_mode == 'FIRST':
                        break
        # If all states deferred, report as unknown
        return state_value or self.parent._unknown

    def _setpoint_md_update(
        self,
        *args,
        write_access: Optional[bool] = None,
        **kwargs
    ) -> None:
        """
        Metadata callback for us to keep track of write access permissions.

        This metadata is used by ophyd and typhos to help give us better
        feedback about write access without needing to try to put a value
        first.
        """
        if write_access is not None:
            self._metadata['write_access'] = write_access
            self._run_metadata_callbacks()

    def put(self, value: Union[int, str], **kwargs) -> None:
        """
        Redirect puts to moving the parent PVStatePositioner device.
        """
        self.parent.move(value, **kwargs)


class MultiDerivedSignal(AggregateSignal):
    """
    Signal derived from multiple signals in the device hierarchy.

    Requires a calculation function to be passed in. Support writing to
    multiple signals if an additional ``calculate_on_put`` function is
    supplied.

    Functions may also be defined in a subclass for advanced or repeated usage.

    Functions may or may be methods.  If ``self`` is noted as the first
    argument of your function, it will be assumed to be a method.  ``self``
    will then refer to the ``MultiDerivedSignal`` instance.

    Parameters
    ----------
    attrs : list of str
        Attribute names of signals that are used to generate a value for this
        signal.

    calculate_on_get : MdsCalculationFunction
        A calculation function that takes in a dictionary of signals to values.
        It should be made to return a value of a compatible ophyd data type,
        such as an integer, float, or an array.

    calculate_on_put : MdsOnPutFunction
        A calculation function that allows this MultiDerivedSignal to be
        read-write instead of just read-only.  It should take in a single value
        and return a dictionary of signal-to-value to write, each with a
        compatible ophyd data type, such as an integer, float, or an array.
        Values will be written to simultaneously and result in a single
        ``Status`` object.
    """

    calculate_on_get: MdsOnGetFunction
    calculate_on_put: Optional[MdsOnPutFunction]

    def __init__(
        self,
        *args,
        attrs: list[str],
        calculate_on_get: Optional[MdsOnGetFunction] = None,
        calculate_on_put: Optional[MdsOnPutFunction] = None,
        timeout: Optional[Number] = None,
        settle_time: Optional[Number] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.timeout = timeout
        self.settle_time = settle_time

        if calculate_on_get is not None:
            self.calculate_on_get = utils.maybe_make_method(
                calculate_on_get, owner=self.parent
            )
        elif not hasattr(self, "calculate_on_get"):
            raise ValueError(
                "The `calculate_on_get` argument must be provided for "
                "non-subclassed MultiDerivedSignal instances.  This function "
                "should have the following signature: "
                "calculate_on_get(mds, items) "
                "where ``mds`` is this signal and ``items`` is a dictionary "
                "of the source signal-to-values items."
            )

        if calculate_on_put is not None:
            if isinstance(self, SignalRO):
                raise ValueError(
                    f"Read-only signal classes ({type(self).__name__}) cannot"
                    f" use a ``calculate_on_put`` function.  Did you mean to "
                    f"use MultiDerivedSignal instead of MultiDerivedSignalRO?"
                )

            self.calculate_on_put = utils.maybe_make_method(
                calculate_on_put,
                owner=self.parent
            )
        elif type(self) is MultiDerivedSignal:
            self._metadata["write_access"] = False
            self.calculate_on_put = None

        self._check_calculate_on_get_signature(self.calculate_on_get)
        if not isinstance(self, SignalRO):
            self._check_calculate_on_put_signature(self.calculate_on_put)

        self.attrs = list(attrs)
        if len(self.attrs) == 0:
            raise ValueError(
                "At least one attribute name must be supplied for a "
                "MultiDerivedSignal.  Also consider using DerivedSignal "
                "directly for the one-to-one case."
            )

        for attr_name in self.attrs:
            self.add_signal_by_attr_name(attr_name)

    def _check_calculate_on_get_signature(self, func: MdsOnGetFunction):
        """Ensure the ``calculate_on_get`` signature is correct."""
        if func is None:
            return

        sig = inspect.signature(func)
        parent_name = getattr(self.parent, "name", "(no parent)")
        func_name = getattr(func, "__name__", "unknown_function")

        try:
            sig.bind(mds=None, items=None)
        except Exception:
            raise ValueError(
                f"The `calculate_on_get` signature is incorrect for "
                f"MultiDerivedSignal.  It should take two parameters, "
                f"'mds' and 'items' as either positional or keyword "
                f"arguments. For {parent_name}.{self.attr_name}:"
                f"{func_name}{sig}"
            )

    def _check_calculate_on_put_signature(
        self, func: Optional[MdsOnGetFunction]
    ):
        """Ensure the ``calculate_on_put`` signature is correct."""
        if func is None:
            return

        sig = inspect.signature(func)
        parent_name = getattr(self.parent, "name", "(no parent)")
        func_name = getattr(func, "__name__", "unknown_function")

        try:
            sig.bind(mds=None, value=None)
        except Exception:
            raise ValueError(
                f"The `calculate_on_put` signature is incorrect for "
                f"MultiDerivedSignal.  It should take two parameters, "
                f"'mds' and 'value' as either positional or keyword "
                f"arguments. For {parent_name}.{self.attr_name}:"
                f"{func_name}{sig}"
            )

    @property
    def signals(self) -> List[Signal]:
        """The signals used to calculate_on_get this MultiDerivedSignal."""
        return list(self._signals)

    def _calc_readback(self) -> OphydDataType:
        """calculate_on_get the new readback value."""
        items = {sig: siginfo.value for sig, siginfo in self._signals.items()}
        return self.calculate_on_get(mds=self, items=items)

    def put(
        self,
        value: OphydDataType,
        callback: Optional[OphydCallback] = None,
        timeout: Union[Number, object] = DEFAULT_WRITE_TIMEOUT,
        settle_time: Optional[float] = None,
        **kwargs
    ) -> ophyd.status.StatusBase:
        """
        calculate_on_get new values for the given derived signals and write.

        Keyword arguments outside of the listed parameters are ignored for
        ophyd ``Signal.put()`` compatibility.

        Parameters
        ----------
        value : OphydDataType
            The value to set.  This is sent to the ``calculate_on_put``
            function to determine which values to write to which signals.
        callback : callable
            Callback for when the put has completed.
        timeout : float, optional
            Timeout before assuming that put has failed.
        settle_time : float, optional
            Time after writing to wait before indicating the put has completely
            finished.
        """
        if timeout is DEFAULT_WRITE_TIMEOUT:
            timeout = self.timeout
        if settle_time is DEFAULT_WRITE_TIMEOUT:
            settle_time = self.settle_time
        st = self.set(value, timeout=timeout, settle_time=settle_time)
        if callback is not None:
            st.add_callback(callback)
        return st

    def set(
        self,
        value: OphydDataType,
        *,
        timeout: Optional[float] = None,
        settle_time: Optional[float] = None
    ) -> ophyd.status.StatusBase:
        if self.calculate_on_put is None:
            raise ReadOnlyError(
                f"{self.name} is read-only. "
                f"`calculate_on_put` function not defined for {self.name} "
                f"({type(self).__name__})."
            )
        to_write = self.calculate_on_put(mds=self, value=value) or {}
        if not isinstance(to_write, Mapping):
            raise RuntimeError(
                f"Internal error: "
                f"{self.calculate_on_put.__name__} for {self.name} failed to "
                f"return an appropriate signal-to-value dictionary. Got: "
                f"{type(to_write).__name__}.  Please contact your POC to get "
                f"this issue fixed."
            )
        return utils.set_many(to_write, owner=self)


class MultiDerivedSignalRO(SignalRO, MultiDerivedSignal):
    """Read-only variant of a MultiDerivedSignal."""
    ...


class AvgSignal(Signal):
    """
    Signal that acts as a rolling average of another signal.

    This will subscribe to a signal, and fill an internal buffer with values
    from `SUB_VALUE`. It will update its own value to be the mean of the last n
    accumulated values, up to the buffer size. If we haven't filled this
    buffer, this will still report a mean value composed of all the values
    we've receieved so far.

    Warning: this means that if we only have recieved ONE value, the mean will
    just be the mean of a single value!

    Parameters
    ----------
    signal : Signal
        Any subclass of `ophyd.signal.Signal` that returns a numeric value.
        This signal will be subscribed to be `AvgSignal` to calculate the mean.

    averages : int
        The number of `SUB_VALUE` updates to include in the average. New values
        after this number is reached will begin overriding old values.
    """

    def __init__(self, signal, averages, *, name, parent=None, **kwargs):
        super().__init__(name=name, parent=parent, **kwargs)
        if isinstance(signal, str):
            signal = getattr(parent, signal)
        self.raw_sig = signal
        self._lock = RLock()
        self.averages = averages
        self.raw_sig.subscribe(self._update_avg)

    @property
    def connected(self):
        return self.raw_sig.connected

    @property
    def averages(self):
        """The size of the internal buffer of values to average over."""
        return self._avg

    @averages.setter
    def averages(self, avg):
        """Reinitialize an empty internal buffer of size `avg`."""
        with self._lock:
            self._avg = avg
            self.index = 0
            # Allocate uninitalized array
            self.values = np.empty(avg)
            # Fill with nan
            self.values.fill(np.nan)

    def _update_avg(self, *args, value, **kwargs):
        """Add new value to the buffer, overriding old values if needed."""
        with self._lock:
            self.values[self.index] = value
            self.index = (self.index + 1) % len(self.values)
            # This takes a mean, skipping nan values.
            self.put(np.nanmean(self.values))


class NotImplementedSignal(SignalRO):
    """Dummy signal for a not implemented feature."""

    def __init__(self, *args, **kwargs):
        kwargs.pop('value', None)
        super().__init__(value='Not implemented', **kwargs)


class InternalSignal(SignalRO):
    """
    Class Signal that stores info but should only be updated by the class.

    SignalRO can be updated with _readback, but this does not process
    callbacks. For the signal to behave normally, we need to bypass the put
    override.

    To put to one of these signals, simply call put with force=True
    """

    def put(self, value, *, timestamp=None, force=False):
        return Signal.put(self, value, timestamp=timestamp, force=force)

    def set(self, value, *, timestamp=None, force=False):
        return Signal.set(self, value, timestamp=timestamp, force=force)


class _OptionalEpicsSignal(Signal):
    """
    An EPICS Signal which may or may not exist.

    The init parameters mirror those of :class:`~ophyd.EpicsSignal`.

    Notes
    -----
    This should be considered for internal use only, and not for
    user-facing device components.  If you use this in your new device,
    there is a good chance we will reject your PR.
    """

    def __init__(self, read_pv, write_pv=None, *, name, parent=None, kind=None,
                 **kwargs):
        self._saw_connection = False
        self._epics_signal = EpicsSignal(
            read_pv=read_pv, write_pv=write_pv, parent=self, name=name,
            kind=kind, **kwargs
        )
        super().__init__(name=name, parent=parent, kind=kind)
        self._epics_signal.subscribe(
            self._epics_meta_update,
            event_type=self._epics_signal.SUB_META,
        )

    def _epics_value_update(self, **kwargs):
        """The EpicsSignal value updated."""
        super().put(value=kwargs['value'], timestamp=kwargs['timestamp'],
                    force=True)
        # Note: the above internally calls run_subs
        # self._run_subs(**kwargs)

    def _epics_meta_update(self, sub_type=None, **kwargs):
        """The EpicsSignal metadata updated; reflect that here."""
        self._metadata.update(**kwargs)
        self._run_subs(sub_type=self.SUB_META, **kwargs)

        if not self._saw_connection and kwargs.get('connected', False):
            self._epics_signal.subscribe(self._epics_value_update)
            self._saw_connection = True

    def destroy(self):
        super().destroy()
        self._epics_signal.destroy()
        self._epics_signal = None

    def should_use_epics_signal(self) -> bool:
        """
        Tell `_OptionalEpicsSignal` whether or not to use the `EpicsSignal`.

        By default, the `EpicsSignal` will be used if the PV has connected.

        Note
        ----
        * Subclasses should override this with their own functionality.
        * This value should not change during the lifetime of the
          `_OptionalEpicsSignal`.
        """
        return self._saw_connection

    def _proxy_method(method_name):  # noqa
        """
        Proxy a method from either the EpicsSignal or the superclass Signal.
        """

        def method_selector(self, *args, **kwargs):
            owner = (self._epics_signal if self.should_use_epics_signal()
                     else super())
            return getattr(owner, method_name)(*args, **kwargs)

        return method_selector

    describe = _proxy_method('describe')
    describe_configuration = _proxy_method('describe_configuration')
    get = _proxy_method('get')
    put = _proxy_method('put')
    set = _proxy_method('set')
    read = _proxy_method('read')
    read_configuration = _proxy_method('read_configuration')
    wait_for_connection = _proxy_method('wait_for_connection')

    def _proxy_property(prop_name, value):  # noqa
        """Read-only property proxy for the internal EPICS Signal."""
        def getter(self):
            if self.should_use_epics_signal():
                return getattr(self._epics_signal, prop_name)
            return value

        # Only support read-only properties for now.
        return property(getter)

    connected = _proxy_property('connected', True)
    read_access = _proxy_property('read_access', True)
    write_access = _proxy_property('write_access', True)
    precision = _proxy_property('precision', 4)
    enum_strs = _proxy_property('enum_strs', ())
    limits = _proxy_property('limits', (0, 0))

    @property
    def kind(self):
        """The EPICS signal's kind."""
        return self._epics_signal.kind

    @kind.setter
    def kind(self, value):
        self._epics_signal.kind = value


class NotepadLinkedSignal(_OptionalEpicsSignal):
    """
    Create the notepad metadata dict for usage by pcdsdevices-notepad.
    For further information, see :class:`NotepadLinkedSignal`.

    Parameters
    ----------
    read_pv : str
        The PV to read from.

    write_pv : str, optional
        The PV to write to if different from the read PV.

    notepad_metadata : dict
        Base metadata for the notepad IOC.  This is a required keyword-only
        argument.  May include keys ``{"record_type", "default_value"}``.

    Note
    ----
    Arguments ``attr_name``, ``parent``, and ``name`` are passed in
    automatically by the ophyd Device machinery and do not need to be specified
    here.

    See also
    --------
    For further argument information, see :class:`~ophyd.EpicsSignal`.
    """

    @staticmethod
    def create_notepad_metadata(
            base_metadata, dotted_name, read_pv, write_pv=None, *,
            attr_name=None, parent=None, name=None, **kwargs):
        """
        Create the notepad metadata dict for usage by pcdsdevices-notepad.
        For further information, see :class:`NotepadLinkedSignal`.
        """
        return dict(
            **base_metadata,
            read_pv=read_pv,
            write_pv=write_pv,
            name=name,
            owner_type=type(parent).__name__,
            dotted_name=dotted_name,
            signal_kwargs={key: value
                           for key, value in kwargs.items()
                           if isinstance(value, (int, str, float))
                           },
        )

    def __init__(self, read_pv, write_pv=None, *, notepad_metadata,
                 attr_name=None, parent=None, name=None, **kwargs):
        # Pre-define some attributes so we can aggregate information:
        self._parent = parent
        self._attr_name = attr_name
        self._name = name
        if self.root is self:
            full_dotted_name = attr_name
        else:
            full_dotted_name = f'{self.root.name}.{attr_name}'

        self.notepad_metadata = self.create_notepad_metadata(
            base_metadata=notepad_metadata,
            dotted_name=full_dotted_name,
            read_pv=read_pv, write_pv=write_pv, name=name, parent=parent,
            **kwargs
        )
        super().__init__(read_pv=read_pv, write_pv=write_pv, parent=parent,
                         attr_name=attr_name, name=name, **kwargs)


class FakeNotepadLinkedSignal(FakeEpicsSignal):
    """A suitable fake class for NotepadLinkedSignal."""
    def __init__(self, read_pv, write_pv=None, *, notepad_metadata,
                 attr_name=None, parent=None, name=None,
                 **kwargs):
        # Pre-define some attributes so we can aggregate information:
        self._parent = parent
        self._attr_name = attr_name
        self.notepad_metadata = NotepadLinkedSignal.create_notepad_metadata(
            base_metadata=notepad_metadata,
            dotted_name=self.root.name + '.' + self.dotted_name,
            read_pv=read_pv, write_pv=write_pv, name=name, parent=parent,
            **kwargs
        )
        super().__init__(read_pv=read_pv, write_pv=write_pv, parent=parent,
                         attr_name=attr_name, name=name, **kwargs)


# NOTE: This is an *on-import* update of the ophyd "fake" device cache
fake_device_cache[NotepadLinkedSignal] = FakeNotepadLinkedSignal


class UnitConversionDerivedSignal(DerivedSignal):
    """
    A DerivedSignal which performs unit conversion.

    Custom units may be specified for the original signal, or if specified, the
    original signal's units may be retrieved upon first connection.

    Parameters
    ----------
    derived_from : Signal or str
        The signal from which this one is derived.  This may be a string
        attribute name that indicates a sibling to use.  When used in a
        ``Device``, this is then simply the attribute name of another
        ``Component``.

    derived_units : str
        The desired units to use for this signal.  These can also be referred
        to as the "user-facing" units.

    original_units : str, optional
        The units from the original signal.  If not specified, control system
        information regarding units will be retrieved upon first connection.

    user_offset : any, optional
        An optional user offset that will be *subtracted* when updating the
        original signal, and *added* when calculating the derived value.
        This offset should be supplied in ``derived_units`` and not
        ``original_units``.

        For example, if the original signal updates to a converted value of
        500 ``derived_units`` and the ``user_offset`` is set to 100, this
        ``DerivedSignal`` will show a value of 600.  When providing a new
        setpoint, the ``user_offset`` will be subtracted.

    write_access : bool, optional
        Write access may be disabled by setting this to ``False``, regardless
        of the write access of the underlying signal.

    name : str, optional
        The signal name.

    parent : Device, optional
        The parent device.  Required if ``derived_from`` is an attribute name.

    limits : 2-tuple, optional
        Ophyd signal-level limits in derived units.  DerivedSignal defaults
        to converting the original signal's limits, but these may be overridden
        here without modifying the original signal.

    **kwargs :
        Keyword arguments are passed to the superclass.
    """

    derived_units: str
    original_units: str

    def __init__(self, derived_from, *,
                 derived_units: str,
                 original_units: typing.Optional[str] = None,
                 user_offset: typing.Optional[numbers.Real] = 0,
                 limits: typing.Optional[typing.Tuple[numbers.Real,
                                                      numbers.Real]] = None,
                 **kwargs):
        self.derived_units = derived_units
        self.original_units = original_units
        self._user_offset = user_offset
        self._custom_limits = limits
        super().__init__(derived_from, **kwargs)
        self._metadata['units'] = derived_units

        # Ensure that we include units in metadata callbacks, even if the
        # original signal does not include them.
        if 'units' not in self._metadata_keys:
            self._metadata_keys = self._metadata_keys + ('units', )

    def forward(self, value):
        '''Compute derived signal value -> original signal value'''
        if self.user_offset is None:
            raise ValueError(f'{self.name} must be set to a non-None value.')
        return convert_unit(value - self.user_offset,
                            self.derived_units, self.original_units)

    def inverse(self, value):
        '''Compute original signal value -> derived signal value'''
        if self.user_offset is None:
            raise ValueError(f'{self.name} must be set to a non-None value.')
        return convert_unit(value, self.original_units,
                            self.derived_units) + self.user_offset

    @property
    def limits(self):
        '''
        Defaults to limits from the original signal (low, high).

        Limit values may be reversed such that ``low <= value <= high`` after
        performing the calculation.

        Limits may also be overridden here without affecting the original
        signal.
        '''
        if self._custom_limits is not None:
            return self._custom_limits

        # Fall back to the superclass derived_from limits:
        return tuple(
            sorted(self.inverse(v) for v in self._derived_from.limits)
        )

    @limits.setter
    def limits(self, value):
        if value is None:
            self._custom_limits = None
            return

        if len(value) != 2 or value[0] >= value[1]:
            raise ValueError('Custom limits must be a 2-tuple (low, high)')

        self._custom_limits = tuple(value)

    @property
    def user_offset(self) -> typing.Optional[typing.Any]:
        """A user-specified offset in *derived*, user-facing units."""
        return self._user_offset

    @user_offset.setter
    def user_offset(self, offset):
        offset_change = -self._user_offset + offset
        self._user_offset = offset
        self._recalculate_position()
        if self._custom_limits is not None:
            self._custom_limits = (
                self._custom_limits[0] + offset_change,
                self._custom_limits[1] + offset_change,
            )

    def _recalculate_position(self):
        """
        Recalculate the derived position and send subscription updates.

        No-operation if the original signal is not connected.
        """
        if not self._derived_from.connected:
            return

        value = self._derived_from.get()
        if value is not None:
            # Note: no kwargs here; no metadata updates
            self._derived_value_callback(value)

    def _derived_metadata_callback(self, *, connected, **kwargs):
        if connected and 'units' in kwargs:
            if self.original_units is None:
                self.original_units = kwargs['units']
        # Do not pass through units, as we have our own.
        kwargs['units'] = self.derived_units
        super()._derived_metadata_callback(connected=connected, **kwargs)

    def describe(self):
        full_desc = super().describe()
        desc = full_desc[self.name]
        desc['units'] = self.derived_units
        # Note: this should be handled in ophyd:
        for key in ('lower_ctrl_limit', 'upper_ctrl_limit'):
            if key in desc:
                desc[key] = self.inverse(desc[key])
        return full_desc


class SignalEditMD(Signal):
    """
    Subclass for allowing an external override of signal metadata.

    This can be useful in cases where the signal metadata is wrong, not
    included properly in the signal, or where you'd like different
    metadata-dependent behavior than what is discovered via the cl.

    Does some minimal checking against the signal's metadata keys and ensures
    the override values always take priority over the normally found values.
    """
    def _override_metadata(self, **md):
        """
        Externally override the signal metadata.

        This is a semi-private member that should only be called from device
        classes on their own signals.
        """
        for key in md.keys():
            if key not in self._metadata_keys:
                raise ValueError(
                    f'Tried to override metadata key {key} in {self.name}, '
                    'but this is not one of the metadata keys: '
                    f'{self._metadata_keys}'
                    )
        try:
            self._metadata_override.update(**md)
        except AttributeError:
            self._metadata_override = md
        self._run_metadata_callbacks()

    @property
    def metadata(self):
        md = {}
        md.update(self._metadata)
        try:
            md.update(self._metadata_override)
        except AttributeError:
            pass
        return md

    # Switch out _metadata for metadata
    def _run_metadata_callbacks(self):
        self._metadata_thread_ctx.run(self._run_subs, sub_type=self.SUB_META,
                                      **self.metadata)


class EpicsSignalBaseEditMD(EpicsSignalBase, SignalEditMD):
    """
    EpicsSignal variant which allows for user correction of various metadata.

    Parameters
    ----------
    enum_strings : list of str, optional
        List of enum strings to replace the EPICS originals.  May not be
        used in conjunction with the dynamic ``enum_attrs``.

    enum_attrs : list of str, optional
        List of signal attribute names, relative to the parent device.  That is
        to say a given attribute is assumed to be a sibling of this signal
        instance.  Attribute names may be ``None`` in the case where the
        original enum string should be passed through.

    See Also
    ---------
    `ophyd.signal.EpicsSignal` for further parameter information.
    """
    _enum_attrs: list[Optional[str]]
    _enum_count: int
    _enum_strings: list[str]
    _original_enum_strings: list[str]
    _enum_signals: list[Optional[ophyd.ophydobj.OphydObject]]
    _enum_string_override: bool
    _enum_subscriptions: dict[ophyd.ophydobj.OphydObject, int]
    _pending_signals: set[ophyd.ophydobj.OphydObject]
    _sent_first_md_callbacks: bool

    def __init__(
        self,
        *args,
        enum_attrs: Optional[list[Optional[str]]] = None,
        enum_strs: Optional[list[str]] = None,
        parent: Optional[ophyd.ophydobj.OphydObject] = None,
        name: Optional[str] = None,
        **kwargs
    ):
        self._enum_attrs = list(enum_attrs or [])
        self._pending_signals = set()
        self._original_enum_strings = []
        self._enum_signals = []
        self._enum_subscriptions = {}
        self._enum_count = 0
        self._metadata_override = {}
        self._sent_first_md_callbacks = False

        if enum_attrs and enum_strs:
            raise ValueError(
                "enum_attrs OR enum_strs may be set, but not both"
            )

        self._enum_string_override = bool(enum_attrs or enum_strs)
        if self._enum_string_override:
            # We need to control 'connected' status based on other signals
            self._metadata_override["connected"] = False

        if enum_attrs:
            # Override by way of other signals
            self._enum_strings = [""] * len(self.enum_attrs)
            # The following magic is provided by EpicsSignalBaseEditMD.
            # The end result is:
            # -> self.metadata["enum_strs"] => self._enum_strings
            self._metadata_override["enum_strs"] = self._enum_strings
            if parent is None:
                raise RuntimeError(
                    "This signal {name!r} must be used in a "
                    "Device/Component hierarchy."
                )

        elif enum_strs:
            # Override with strings
            self._enum_strings = list(enum_strs)
            self._metadata_override["enum_strs"] = self._enum_strings

        super().__init__(*args, parent=parent, name=name, **kwargs)

        if enum_attrs:
            # NOTE: Ensure that subscriptions happen only after everything
            # else is already configured.
            self._subscribe_enum_attrs()

    def destroy(self):
        super().destroy()
        for sig, sub in self._enum_subscriptions.items():
            if sig is not None:
                sig.unsubscribe(sub)
        self._enum_subscriptions.clear()

    def _subscribe_enum_attrs(self):
        """Subscribe to enum signals by attribute name."""
        for attr in self.enum_attrs:
            if attr is None:
                # Opt-out for a specific signal
                self._enum_signals.append(None)
                continue

            try:
                obj = getattr(self.parent, attr)
            except AttributeError as ex:
                raise RuntimeError(
                    f"Attribute {attr!r} specified in enum list appears to be "
                    f"invalid for the device {self.parent.name}."
                ) from ex

            if obj is self:
                raise RuntimeError(
                    f"Recursively specified {self.name!r} in the enum_attrs "
                    "list.  Don't do that."
                )
            self._enum_signals.append(obj)
            self._pending_signals.add(obj)
            self._enum_subscriptions[obj] = obj.subscribe(
                self._enum_string_updated, run=True
            )

    # Switch out _metadata for metadata where appropriate
    @property
    def enum_strs(self) -> list[str]:
        """
        List of enum strings.

        For an EpicsSignalEditMD, this could be one of:

        1. The original enum strings from the PV
        2. The strings found from the respective signals referenced by
            ``enum_attrs``.
        3. The user-provided strings in ``enum_strs``.
        """
        if self._enum_string_override:
            return list(self._enum_strings)[:self._enum_count]
        return self.metadata['enum_strs']

    @property
    def precision(self):
        """The PV precision as reported by EPICS (or EpicsSignalEditMD)."""
        return self.metadata['precision']

    @property
    def limits(self) -> tuple[numbers.Real, numbers.Real]:
        """The PV limits as reported by EPICS (or EpicsSignalEditMD)."""
        return (self.metadata['lower_ctrl_limit'],
                self.metadata['upper_ctrl_limit'])

    def describe(self):
        """
        Return the signal description as a dictionary.

        Units, limits, precision, and enum strings may be overridden.

        Returns
        -------
        dict
            Dictionary of name and formatted description string
        """
        desc = super().describe()
        desc[self.name]['units'] = self.metadata['units']
        return desc

    @property
    def enum_attrs(self) -> list[str]:
        """Enum attribute names - the source of each enum string."""
        return list(self._enum_attrs)

    def _enum_string_updated(
        self,
        value: str,
        obj: ophyd.ophydobj.OphydObject,
        **kwargs
    ):
        """
        A single Signal from ``enum_signals`` updated its value.

        This is a ``SUB_VALUE`` subscription callback from that signal.

        Parameters
        ----------
        value : str
            The value of that enum index.

        obj : ophyd.ophydobj.OphydObject
            The ophyd object with the value.

        **kwargs :
            Additional metadata from ``self._metadata``.
        """
        if value is None:
            # The callback may run before it's connected
            return

        try:
            idx = self._enum_signals.index(obj)
        except IndexError:
            return

        if value == "Invalid":
            try:
                value = self._original_enum_strings[idx]
            except IndexError:
                ...

        self._enum_strings[idx] = str(value)

        self.log.debug(
            "Got enum %s [%d] = %s from %s",
            self.name, idx, value, getattr(obj, "pvname", "(no pvname)")
        )
        try:
            self._pending_signals.remove(obj)
        except KeyError:
            ...

        if not self._pending_signals:
            # We're probably connected!
            self._run_metadata_callbacks()

    @property
    def connected(self) -> bool:
        """Is the signal connected and ready to use?"""
        return (
            self._metadata["connected"]
            and not self._destroyed
            and not len(self._pending_signals)
        )

    def _check_signal_metadata(self):
        """Check the original enum strings to compare the attributes."""
        if not self._enum_string_override:
            return

        self._original_enum_strings = self._metadata.get(
            "enum_strs", None
        ) or []
        if not self._original_enum_strings:
            self.log.error(
                "No enum strings on %r; was %r used inappropriately?",
                self.pvname, type(self).__name__
            )
            return

        if self._enum_count == 0:
            self._enum_count = len(self._original_enum_strings)

            def pick_enum_string(existing: str, original: str) -> str:
                """
                Pick the best enum string, given two options.

                The "Invalid" marker indicates that the PLC sName for the state
                has not yet been updated.  Ignore it and fall back to the
                PLC enum-defined value.
                """
                if existing.lower() == "invalid":
                    existing = ""
                return existing or original

            # Only update ones that have yet to be populated;  this can
            # be a race for who connects first:
            updated_enums = [
                pick_enum_string(existing, original)
                for existing, original in itertools.zip_longest(
                    self._enum_strings,
                    self._original_enum_strings,
                    fillvalue=""
                )
            ]
            self._enum_strings[:] = updated_enums

    def _run_metadata_callbacks(self):
        """Hook for metadata callbacks, mostly run by superclasses."""
        self._metadata_override["connected"] = self.connected
        # TODO: to truncate the number of enum strings reported to the number
        # that EPICS reports for the given PV, the following may be advisable.
        # However, it seems to add additional confusing errors; so consider
        # this a todo.
        # self._metadata_override["enum_strs"] = self.enum_strs
        if self._metadata["connected"]:
            # The underlying PV has connected - check its enum_strs:
            self._check_signal_metadata()
        if self.connected or self._sent_first_md_callbacks:
            self._sent_first_md_callbacks = True
            super()._run_metadata_callbacks()


class EpicsSignalEditMD(EpicsSignal, EpicsSignalBaseEditMD):
    pass


class EpicsSignalROEditMD(EpicsSignalRO, EpicsSignalBaseEditMD):
    pass


EpicsSignalEditMD.__doc__ = EpicsSignalBaseEditMD.__doc__ + EpicsSignal.__doc__
EpicsSignalROEditMD.__doc__ = (
    EpicsSignalBaseEditMD.__doc__ + EpicsSignalRO.__doc__
)


class FakeEpicsSignalEditMD(SignalEditMD, FakeEpicsSignal):
    """
    API stand-in for EpicsSignalEditMD
    Add to this if you need it to actually work for your test.
    """
    def __init__(
        self,
        *args,
        enum_attrs: Optional[list[Optional[str]]] = None,
        enum_strs: Optional[list[str]] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._enum_attrs = enum_attrs
        self._enum_strs = enum_strs

    @property
    def enum_attrs(self):
        return self._enum_attrs

    @property
    def enum_strs(self):
        return self._enum_attrs or self._enum_strs or None

    @property
    def limits(self) -> tuple[numbers.Real, numbers.Real]:
        """
        Override limits because EpicsSignalEditMD overrides the limits.

        If defined in the test, do it like in the real EpicsSignalEditMD.
        Otherwise, be permissive to avoid false test failures.
        """
        lower = self.metadata['lower_ctrl_limit']
        upper = self.metadata['upper_ctrl_limit']
        if None in (lower, upper):
            return (0, 0)
        else:
            return (lower, upper)


class FakeEpicsSignalROEditMD(FakeEpicsSignalEditMD, FakeEpicsSignalRO):
    """
    API stand-in for EpicsSignalROEditMD
    """


fake_device_cache[EpicsSignalEditMD] = FakeEpicsSignalEditMD
fake_device_cache[EpicsSignalROEditMD] = FakeEpicsSignalROEditMD
