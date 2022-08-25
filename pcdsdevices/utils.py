from __future__ import annotations

import enum
import inspect
import logging
import operator
import select
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Iterable
from functools import reduce
from types import MethodType
from typing import Callable, Dict, Iterator, List, Optional, Union

import ophyd
import prettytable
from ophyd.device import Component as Cpt
from ophyd.device import Device
from ophyd.ophydobj import Kind

from ._html import collapse_list_head, collapse_list_tail
from .type_hints import Number, OphydDataType

try:
    import termios
    import tty
except ImportError:
    tty = None
    termios = None

logger = logging.getLogger(__name__)

arrow_up = '\x1b[A'
arrow_down = '\x1b[B'
arrow_right = '\x1b[C'
arrow_left = '\x1b[D'
shift_arrow_up = '\x1b[1;2A'
shift_arrow_down = '\x1b[1;2B'
shift_arrow_right = '\x1b[1;2C'
shift_arrow_left = '\x1b[1;2D'
alt_arrow_up = '\x1b[1;3A'
alt_arrow_down = '\x1b[1;3B'
alt_arrow_right = '\x1b[1;3C'
alt_arrow_left = '\x1b[1;3D'
ctrl_arrow_up = '\x1b[1;5A'
ctrl_arrow_down = '\x1b[1;5B'
ctrl_arrow_right = '\x1b[1;5C'
ctrl_arrow_left = '\x1b[1;5D'
plus = '+'
minus = '-'


def is_input():
    """
    Utility to check if there is input available.

    Returns
    -------
    is_input : bool
        `True` if there is data in `sys.stdin`.
    """

    return select.select([sys.stdin], [], [], 1) == ([sys.stdin], [], [])


def get_input():
    """
    Waits for a single character input and returns it.

    You can compare the input to the keys stored in this module e.g.
    ``utils.arrow_up == get_input()``.

    Returns
    -------
    input : str
    """
    if termios is None:
        raise RuntimeError('Not supported on this platform')

    # Save old terminal settings
    old_settings = termios.tcgetattr(sys.stdin)
    # Stash a None here in case we get interrupted
    inp = None
    try:
        # Swap to cbreak mode to get raw inputs
        tty.setcbreak(sys.stdin.fileno())
        # Poll for input. This is interruptable with ctrl+c
        while (not is_input()):
            time.sleep(0.01)
        # Read the first character
        inp = sys.stdin.read(1)
        # Read more if we have a control sequence
        if inp == '\x1b':
            extra_inp = sys.stdin.read(2)
            inp += extra_inp
            # Read even more if we had a shift/alt/ctrl modifier
            if extra_inp == '[1':
                inp += sys.stdin.read(3)
    finally:
        # Restore the terminal to normal input mode
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        return inp


ureg = None


def convert_unit(value, unit, new_unit):
    """
    One-line unit conversion.

    Parameters
    ----------
    value : float
        The starting value for the conversion.

    unit : str
        The starting unit for the conversion.

    new_unit : str
        The desired unit for the conversion.

    Returns
    -------
    new_value : float
        The starting value, but converted to the new unit.
    """

    global ureg
    if ureg is None:
        import pint
        ureg = pint.UnitRegistry()

    expr = ureg.parse_expression(unit)
    return (value * expr).to(new_unit).magnitude


def ipm_screen(dettype, prefix, prefix_ioc):
    """
    Function to call the (pyQT) screen for an IPM box.

    Parameters
    ----------
    dettype : {'IPIMB', 'Wave8'}
        The type of detector being accessed.

    prefix : str
        The PV prefix associated with the device being accessed.

    prefix_ioc : str
        The PV prefix associated with the IOC running the device.
    """

    if (dettype == 'IPIMB'):
        executable = '/reg/g/pcds/controls/pycaqt/ipimb/ipimb'
    elif (dettype == 'Wave8'):
        executable = '/reg/g/pcds/pyps/apps/wave8/latest/wave8'
    else:
        raise ValueError('Unknown detector type')
    if shutil.which(executable) is None:
        raise EnvironmentError('%s is not on path, we cannot start the screen'
                               % executable)

    logger.info(f'Opening {dettype} screen for {prefix}...')
    arglist = [executable, '--base', prefix, '--ioc', prefix_ioc,
               '--evr', prefix+':TRIG']
    _ = subprocess.Popen(arglist)


def get_component(obj):
    """
    Get the component that made the given object.

    Parameters
    ----------
    obj : ophyd.OphydItem
        The ophyd item for which to get the component.

    Returns
    -------
    component : ophyd.Component
        The component, if available.
    """
    if obj.parent is None:
        return None

    return getattr(type(obj.parent), obj.attr_name, None)


def schedule_task(func, args=None, kwargs=None, delay=None):
    """
    Use ophyd's dispatcher to schedule a task for later.

    This is basically the function I was hoping to find in ophyd.
    Schedules a task for the utility thread if we're in some arbitrary thread,
    schedules a task for the same thread if we're in one of ophyd's callback
    queues already.
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}

    dispatcher = ophyd.cl.get_dispatcher()

    # Check if we're already in an ophyd dispatcher thread
    current_thread = threading.currentThread()
    matched_thread = None
    for name, thread in dispatcher.threads.items():
        if thread == current_thread:
            matched_thread = name
            context = dispatcher.get_thread_context(matched_thread)
            break

    def schedule():
        if matched_thread is not None and context.event_thread is not None:
            # Put into same queue
            context.event_thread.queue.put((func, args, kwargs))
        else:
            # Put into utility queue
            dispatcher.schedule_utility_task(func, *args, **kwargs)

    if delay is None:
        # Do it right away
        schedule()
    else:
        # Do it later
        timer = threading.Timer(delay, schedule)
        timer.start()


def get_status_value(status_info, *keys, default_value='N/A'):
    """
    Get the value of a dictionary key.

    Parameters
    ----------
    status_info : dict
        Dictionary to look through.
    keys : list
        List of keys to look through with nested dictionarie.
    default_value : str
        A default value to return if the item value was not found.

    Returns
    -------
    value : dictionary item value
        Value of the last key in the `keys` list.
    """
    try:
        value = reduce(operator.getitem, keys, status_info)
        return value
    except KeyError:
        return default_value


def get_status_float(status_info, *keys, default_value='N/A', precision=4,
                     format='f', scale=1.0, include_plus_sign=False):
    """
    Get the value of a dictionary key.

    Format the value with the precision requested if it is a float value.

    Parameters
    ----------
    status_info : dict
        Dictionary to look through.
    keys : list
        List of keys to look through with nested dictionarie.
    default_value : str, optional
        A default value to return if the item value was not found.
    precision : int, optional
        Precision requested for the float values. Defaults to 4.
    format : str, optional
        Format specifier to use for the floating point value. Defaults to 'f'.
    scale : float, optional
        Scale to apply to value prior to formatting.
    include_plus_sign : bool, optional
        Include a plus sign before a positive value for text alignment
        purposes. Defaults to False.

    Returns
    -------
    value : dictionary item value, or `N/A`
        Value of the last key in the `keys` list formated with precision.
    """
    try:
        value = reduce(operator.getitem, keys, status_info)
        if isinstance(value, (int, float)):
            value = float(value) * scale
            if include_plus_sign:
                fmt = '{:+.%d%s}' % (precision, format)
            else:
                fmt = '{:.%d%s}' % (precision, format)
            return fmt.format(value)
        return value
    except KeyError:
        return default_value


def format_status_table(status_info, row_to_key, column_to_key,
                        row_identifier='Index'):
    """
    Create a PrettyTable based on status information.

    Parameters
    ----------
    status_info : dict
        The status information dictionary.

    row_to_key : dict
        Dictionary of the form ``{'display_text': 'status_key'}``.

    column_to_key : dict
        Dictionary of the form ``{'display_text': 'status_key'}``.

    row_identifier : str, optional
        What to show for the first column, likely an 'Index' or 'Component'.
    """

    table = prettytable.PrettyTable()
    table.field_names = [row_identifier] + list(column_to_key)
    for row_name, row_key in row_to_key.items():
        row = [
            get_status_value(status_info, row_key, key, 'value')
            for key in column_to_key.values()
        ]
        table.add_row([str(row_name)] + row)

    return table


def combine_status_info(obj, status_info, attrs, separator='\n= {attr} ='):
    """
    Combine status information from the given attributes.

    Parameters
    ----------
    obj : OphydObj
        The parent ophyd object.

    status_info : dict
        The status information dictionary.

    attrs : sequence of str
        The attribute names.

    separator : str, optional
        The separator line between the statuses.  May be formatted
        with variables ``attr``, ``parent``, or ``child``.
    """
    lines = []
    for attr in attrs:
        child = getattr(obj, attr)
        lines.append(separator.format(attr=attr, parent=obj, child=child))
        lines.append(child.format_status_info(status_info[attr]))

    return '\n'.join(lines)


def doc_format_decorator(**doc_fmts):
    """
    Decorator for substituting values into a docstring.

    This is useful for cases where we want to include module
    constants in docstrings but we want the docstring to
    update automatically when we decide to change the
    constant.
    """
    def inner_decorator(func):
        func.__doc__ = func.__doc__.format(**doc_fmts)
        return func
    return inner_decorator


EnumId = Union[enum.Enum, int, str]


class HelpfulIntEnumMeta(enum.EnumMeta):
    def __getattr__(self, key):
        if hasattr(key, "lower"):
            for item in self:
                if item.name.lower() == key.lower():
                    return item
        return super().__getattr__(key)

    def __getitem__(self, key):
        if hasattr(key, "lower"):
            for item in self:
                if item.name.lower() == key.lower():
                    return item
        return super().__getitem__(key)


class HelpfulIntEnum(enum.IntEnum, metaclass=HelpfulIntEnumMeta):
    """
    IntEnum subclass with some utility extensions and case insensitivity.
    """

    @classmethod
    def from_any(cls, identifier: EnumId) -> HelpfulIntEnum:
        """
        Try all the ways to interpret identifier as the enum.
        This is intended to consolidate the try/except tree typically used
        to interpret external input as an enum.

        Parameters
        ----------
        identifier : EnumId
            Any str, int, or Enum value that corresponds with a valid value
            on this HelpfulIntEnum instance.

        Returns
        -------
        enum : HelpfulIntEnum
            The corresponding enum object associated with the identifier.
        """
        try:
            return cls[identifier]
        except KeyError:
            return cls(identifier)

    @classmethod
    def include(
        cls,
        identifiers: Iterator[EnumId],
    ) -> set[HelpfulIntEnum]:
        """
        Returns all enum values matching the identifiers given.
        This is a shortcut for calling cls.from_any many times and
        assembling a set of the results.

        Parameters
        ----------
        identifiers : Iterator[EnumId]
            Any iterable that contains strings, ints, and Enum values that
            correspond with valid values on this HelpfulIntEnum instance.

        Returns
        -------
        enums : set[HelpfulIntEnum]
            A set whose elements are the enum objects associated with the
            input identifiers.
        """
        return {cls.from_any(ident) for ident in identifiers}

    @classmethod
    def exclude(
        cls,
        identifiers: Iterator[EnumId],
    ) -> set[HelpfulIntEnum]:
        """
        Return all enum values other than the ones given.

        Parameters
        ----------
        identifiers : Iterator[EnumId]
            Any iterable that contains strings, ints, and Enum values that
            correspond with valid values on this HelpfulIntEnum instance.

        Returns
        -------
        enums : set[HelpfulIntEnum]
            A set whose elements are the valid enum objects not associated
            with the input identifiers.
        """
        return set(cls.__members__.values()) - cls.include(identifiers)


def set_many(
    to_set: Dict[ophyd.Signal, OphydDataType],
    *,
    owner: Optional[ophyd.ophydobj.OphydObject] = None,
    timeout: Optional[Number] = None,
    settle_time: Optional[Number] = None,
    raise_on_set_failure: bool = False
) -> ophyd.status.StatusBase:
    """
    Call ``set`` on all given signal-to-value pairs with a single Status
    return value.

    Parameters
    ----------
    to_set : Dict[ophyd.Signal, OphydDataType]
        Dictionary of Signal to data to ``set``.

    owner : OphydObject, optional
        The owner object, to be used for logging / Status object attribution.

    timeout : float, optional
        Per-signal timeout to configure during set.

    settle_time : float, optional
        Per-signal settle time to configure during set.

    raise_on_set_failure : bool, optional
        Raise if any of the ``set`` calls fail.

    Returns
    -------
    status : ophyd.Status.StatusBase
        One Status or AndStatus instance that reflects the completion status of
        the setting all signal to the provided values.
    """
    statuses = []
    log = owner.log if owner is not None else logger
    for signal, value in to_set.items():
        try:
            st = signal.set(
                value, timeout=timeout, settle_time=settle_time
            )
        except Exception:
            log.exception(
                "Failed to set %s to %s", signal.name, value
            )
            if raise_on_set_failure:
                raise
        else:
            statuses.append(st)

    if not statuses:
        st = ophyd.status.Status(obj=owner)
        st.set_finished()
        return st

    status = statuses[0]
    for st in statuses[1:]:
        status = ophyd.status.AndStatus(status, st)
    return status


def maybe_make_method(
    func: Optional[Callable], owner: object
) -> Optional[Callable]:
    """
    Bind ``func`` as a method of ``owner`` if ``self`` is the first parameter.

    Additionally, this accepts ``None`` and passes it through.

    Parameters
    ----------
    func : callable or None
        The function to optionally wrap.

    owner : object
        The owner class instance to optionally bind ``func`` to.

    Returns
    -------
    maybe_method : callable or None
        A callable function or method, depending on the signature of ``func``.
    """
    if func is None:
        return None

    if not callable(func):
        raise ValueError(
            f"The provided ``func`` is not callable: {func!r} is of "
            f"type {type(func).__name__}"
        )

    sig = inspect.signature(func)
    if "self" in sig.parameters and list(sig.parameters)[0] == "self":
        return MethodType(func, owner)
    return func


def format_ophyds_to_html(obj, allow_child=False):
    """
    Recursively construct html that contains the output from .status() for
    each object provided.  Base case is being passed a single ophyd object
    with a `.status()` method.  Any object without a `.status()` method is
    ignored.

    Creates divs and buttons based on styling
    from `nabs._html.collapse_list_head` and `nabs._html.collapse_list_tail`

    Parameters
    ----------
    obj : ophyd object or Iterable of ophyd objects
        Objects to format into html

    allow_child : bool, optional
        Whether or not to post child devices to the elog.  Defaults to False,
        to keep long lists of devices concise

    Returns
    -------
    out : string
        html body containing ophyd object representations (sans styling, JS)
    """
    if isinstance(obj, Iterable):
        content = ""

        for o in obj:
            content += format_ophyds_to_html(o, allow_child=allow_child)

        # Don't return wrapping if there's no content
        if content == "":
            return content

        # HelpfulNamespaces tend to lack names, maybe they won't some day
        parent_default = ('Ophyd status: ' +
                          ', '.join('[...]' if isinstance(o, Iterable)
                                    else o.name for o in obj))
        parent_name = getattr(obj, '__name__', parent_default[:60] + ' ...')

        # Wrap in a parent div
        out = (
            "<button class='collapsible'>" +
            f"{parent_name}" +  # should be a namespace name
            "</button><div class='parent'>" +
            content +
            "</div>"
        )
        return out

    # check if parent level ophyd object
    elif (callable(getattr(obj, 'status', None)) and
            ((getattr(obj, 'parent', None) is None and
              getattr(obj, 'biological_parent', None) is None) or
             allow_child)):
        content = ""
        try:
            content = (
                f"<button class='collapsible'>{obj.name}</button>" +
                f"<div class='child content'><pre>{obj.status()}</pre></div>"
            )
        except Exception as ex:
            logger.info(f'skipped {str(obj)}, due to Exception: {ex}')

        return content

    # fallback base case (if ignoring obj)
    else:
        return ""


def post_ophyds_to_elog(objs, allow_child=False, hutch_elog=None):
    """
    Take a list of ophyd objects and post their status representations
    to the elog.  Handles singular objects, lists of objects, and
    HelpfulNamespace's provided in hutch-python

    .. code-block:: python

        # pass in an object
        post_ophyds_to_elog(at2l0)

        # or a list of objects
        post_ophyds_to_elog([at2l0, im3l0])

        # devices with no parents are ignored by default :(
        post_ophyds_to_elog([at2l0, at2l0.blade_01], allow_child=True)

        # or a HelpfulNamespace
        post_ophyds_to_elog(m)

    Parameters
    ----------
    objs : ophyd object or Iterable of ophyd objects
        Objects to format and post

    allow_child : bool, optional
        Whether or not to post child devices to the elog.  Defaults to False,
        to keep long lists of devices concise

    hutch_elog : HutchELog, optional
        ELog instance to post to.  If not provided, will attempt to grab
        primary registered ELog instance
    """
    if hutch_elog is None:
        try:
            from elog.utils import get_primary_elog
            hutch_elog = get_primary_elog()
        except ValueError:
            logger.info('elog module exists, but no elog registered')
            return
    else:
        logger.info('Posting to provided elog')

    post = format_ophyds_to_html(objs, allow_child=allow_child)

    if post == "":
        logger.info("No valid devices found, no post submitted")
        return

    # wrap post in head and tail
    final_post = collapse_list_head + post + collapse_list_tail

    hutch_elog.post(final_post, tags=['ophyd_status'],
                    title='ophyd status report')


def reorder_components(
    cls: Optional[type[Device]] = None,
    start_with: Optional[List[Union[str, Cpt]]] = None,
    end_with: Optional[List[Union[str, Cpt]]] = None,
) -> Union[type[Device], Callable[[type[Device]], type[Device]]]:
    """
    Rearrange the components in cls for typhos displays.

    Internally, this works by switching around the keys in the _sig_attrs
    OrderedDict.

    Parameters
    ----------
    cls : Device subclass
        The Device subclass that we'd like to rearrange the order of.
    start_with : list of str, optional
        The component names to bring to the top of the screen.
    end_with : list of str, optional
        The component names to bring to the bottom of the screen.

    Returns
    -------
    cls : Device subclass, or function that returns it
        Decorator-compatible output. When used as a function or as a
        no-argument decorator, this will return the input device.
        When used as a decorator with the reverse argument, this will
        return a function as required by the decorator interface.
    """
    # Special decorator handling
    def inner(cls: type[Device]) -> type[Device]:
        start_norm = _normalize_reorder_list(cls, start_with)
        end_norm = _normalize_reorder_list(cls, end_with)
        for cpt_name in reversed(start_norm):
            cls._sig_attrs.move_to_end(cpt_name, last=False)
        for cpt_name in end_norm:
            cls._sig_attrs.move_to_end(cpt_name, last=True)
        return cls

    if cls is not None:
        # For function call or no-args decorator
        return inner(cls)
    # For decorator with args
    return inner


def _normalize_reorder_list(
    cls: type[Device],
    cpts_or_names: Optional[List[Union[str, Cpt]]],
) -> List[str]:
    """
    Simplify the user's variable arguments for the component reordering.
    """
    if cpts_or_names is None:
        return []
    reverse_map = {cpt: name for name, cpt in cls._sig_attrs.items()}
    output = []
    for obj in cpts_or_names:
        if isinstance(obj, Cpt):
            try:
                output.append(reverse_map[obj])
            except KeyError as exc:
                raise ValueError(
                    f'Received component {obj}, which is not from the device '
                    f'class {cls}. We have components with the following '
                    f'names: {", ".join(cls._sig_attrs)}'
                ) from exc
        elif isinstance(obj, str):
            output.append(obj)
        else:
            raise TypeError(
                f'Received object {obj}, which is not a str or Component.'
            )
    return output


def move_subdevices_to_start(
    cls: Optional[type[Device]] = None,
    subdevice_cls: type[Device] = Device,
) -> Union[type[Device], Callable[[type[Device]], type[Device]]]:
    """
    Arrange the component order of a device class to put subdevices first.

    This can be useful to bring e.g. all the motors to the top for the
    typhos screen.

    The relative ordering of subdevices is preserved.

    Parameters
    ----------
    cls : Device subclass
        The Device subclass that we'd like to rearrange the order of.
    subdevice_cls: type, optional
        A specific class type to move to the front. If omitted, all device
        subclasses will be moved.

    Returns
    -------
    cls : Device subclass, or function that returns it
        Decorator-compatible output. When used as a function or as a
        no-argument decorator, this will return the input device.
        When used as a decorator with the subdevice_cls argument, this will
        return a function as required by the decorator interface.
    """
    # Special decorator handling
    def inner(cls: type[Device]) -> type[Device]:
        device_names = []
        for name, cpt in cls._sig_attrs.items():
            if issubclass(cpt.cls, subdevice_cls):
                device_names.append(name)
        reorder_components(cls, start_with=device_names)
        return cls

    if cls is not None:
        # For function call or no-args decorator
        return inner(cls)
    # For decorator with args
    return inner


def sort_components_by_name(
    cls: Optional[type[Device]] = None,
    reverse: bool = False,
) -> Union[type[Device], Callable[[type[Device]], type[Device]]]:
    """
    Arrange the component order of a device class in alphabetical order.

    This can be useful as a first step before bringing specific components
    to the top of the queue for the typhos screen.

    Parameters
    ----------
    cls : Device subclass
        The Device subclass that we'd like to rearrange the order of.
    reverse : bool, optional
        Set to True to sort in descending order instead.

    Returns
    -------
    cls : Device subclass, or function that returns it
        Decorator-compatible output. When used as a function or as a
        no-argument decorator, this will return the input device.
        When used as a decorator with the reverse argument, this will
        return a function as required by the decorator interface.
    """
    # Special decorator handling
    def inner(cls: type[Device]) -> type[Device]:
        alphabetical = list(sorted(cls._sig_attrs, reverse=reverse))
        reorder_components(cls, start_with=alphabetical)
        return cls

    if cls is not None:
        # For function call or no-args decorator
        return inner(cls)
    # For decorator with args
    return inner


def sort_components_by_kind(cls: type[Device]) -> type[Device]:
    """
    Arrange the component order of a device class in kind order.

    Kind order is hinted > normal > config > omitted.

    This can be useful because typically the higher kind classes
    are more important, and therefore should be higher up on the
    typhos screen.

    The relative ordering of subdevices within a kind is preserved.

    This function makes no attempt to disambiguate or sort
    combination kinds. For example:

    - "hinted | config" counts as "hinted"
    - "normal | config" counts as "normal"

    Parameters
    ----------
    cls : Device subclass
        The Device subclass that we'd like to rearrange the order of.

    Returns
    -------
    cls : Device subclass
        The same class from the input, mutated. This is returned so that
        sort_components_by_kind can be used as a class decorator.
    """
    hinted = []
    normal = []
    config = []
    omitted = []
    for name, cpt in cls._sig_attrs.items():
        if check_kind_flag(cpt.kind, Kind.hinted):
            hinted.append(name)
        elif check_kind_flag(cpt.kind, Kind.normal):
            normal.append(name)
        elif check_kind_flag(cpt.kind, Kind.config):
            config.append(name)
        else:
            omitted.append(name)
    reorder_components(cls, end_with=hinted)
    reorder_components(cls, end_with=normal)
    reorder_components(cls, end_with=config)
    reorder_components(cls, end_with=omitted)
    return cls


def check_kind_flag(kind: int, flag: Kind) -> bool:
    """Return True if kind contains flag."""
    return kind & flag == flag


def set_standard_ordering(cls: type[Device]) -> type[Device]:
    """
    Set a sensible "standard" ordering for use in typhos.

    This ordering is:
    - Devices first, then signals
    - Within the above, kind order
    - Within a kind, alphabetical order

    This is not universally applicable and is just a suggested starting point.

    Parameters
    ----------
    cls : Device subclass
        The Device subclass that we'd like to rearrange the order of.

    Returns
    -------
    cls : Device subclass
        The same class from the input, mutated. This is returned so that
        set_standard_ordering can be used as a class decorator.
    """
    sort_components_by_name(cls)
    sort_components_by_kind(cls)
    move_subdevices_to_start(cls)
    return cls
