import collections
import copy
from collections.abc import Iterator
from typing import Any, Optional

from ophyd.areadetector.plugins import PluginBase
from ophyd.device import Component, Device
from ophyd.ophydobj import Kind, OphydObject
from ophyd.pseudopos import PseudoSingle
from ophyd.signal import AttributeSignal, DerivedSignal

from .signal import AggregateSignal, PVStateSignal


class UnrelatedComponent(Component):
    """
    Components that are unrelated to the main ``prefix`` attribute.

    These components each need to have a full prefix specified rather than
    the normal ``suffix`` extension or formatting. This is specified in the
    device's ``**kwargs``, e.g. ``subdevice_prefix='SOME:PV'``.

    The `collect_prefixes` class method is used to gather these special
    prefixes in a convenient one-liner rather than needing to sift through
    formatted components.

    Examples
    --------

    A simple usage example::

        from pcdsdevices.device import UnrelatedComponent as UCpt

        class MyDevice(Device):
            motor1 = UCpt(EpicsMotor)
            motor2 = UCpt(EpicsMotor)

            def __init__(self, prefix, **kwargs):
                UCpt.collect_prefixes(self, kwargs)
                super().__init__(prefix, **kwargs)
    """

    @classmethod
    def collect_prefixes(cls, device, kwargs):
        """
        Gather all the special prefixes from a device's ``**kwargs``.

        This must be called once during the ``__init__`` of a device with
        UnrelatedComponent instances.

        Parameters
        ----------
        device : ~ophyd.device.Device
            The device to gather prefixes for. Typically this is just ``self``.

        kwargs : dict
            The kwargs dictionary with extra prefixes defined.
        """

        device.unrelated_prefixes = {}
        for key, value in list(kwargs.items()):
            if key.endswith('_prefix'):
                device.unrelated_prefixes[key] = value
                kwargs.pop(key)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Needs to be non-None or it gets ignored
        self.suffix = ''
        add_prefix = list(kwargs.get('add_prefix', ['suffix']))

        # Include subdevice UnrelatedComponent
        try:
            walk_iterator = self.cls.walk_components()
        except AttributeError:
            # No subdevices
            walk_iterator = ()

        for cpt_walk in walk_iterator:
            if isinstance(cpt_walk.item, UnrelatedComponent):
                name = cpt_walk.dotted_name.replace('.', '_') + '_prefix'
                add_prefix.append(name)
                self.kwargs[name] = None

        self.add_prefix = tuple(add_prefix)

    def maybe_add_prefix(self, instance, kw, suffix):
        if kw not in self.add_prefix:
            return suffix

        # Primary prefix for UnrelatedComponent
        if kw == 'suffix':
            expected_kwarg = self.attr + '_prefix'
        # Subdevice UnrelatedComponent
        else:
            expected_kwarg = self.attr + '_' + kw
        try:
            return instance.unrelated_prefixes[expected_kwarg]
        except KeyError:
            raise ValueError(f'Missing {expected_kwarg} in __init__ for '
                             f'{instance.name}.')


class ObjectComponent(Component):
    """
    A component that includes an existing instantiated object into a Device.

    Typically, component classes exist as a description of how to create the
    subdevice or signal, and this continues to be the preferred way to
    define Device classes.

    This exists as a convenience tool for one-off devices that need to include
    other pre-instantiated devices as elements.

    .. note::

        Since this picks an object to include at class definition time,
        you should avoid instantiating classes with object components multiple
        times. If you would like to create a re-usable device that includes
        pre-instantiated devices at init time, see `InterfaceDevice`.

    .. note::

        This does not set the ``parent`` attribute on the object, which will
        retain its original ``parent`` despite being adopted here.

    Parameters
    ----------
    obj : object
        Any existing object. This will be included in the Device as a proper
        component, as if it was constructed by the class itself.

    kind : `ophydobj.Kind` or str, optional
        If provided, override the object's kind. In standard components this
        defaults to Kind.normal, but here it will default to "do not change
        the kind, leave it as is". If provided, it is up the user to make sure
        they are being consistent with the setting of kinds on their devices.
    """
    def __init__(self, obj, kind=None):
        self._override_kind = kind
        if kind is None:
            kind = Kind.normal
        super().__init__(obj.__class__, kind=kind)
        self.obj = obj

    def create_component(self, instance):
        if self._override_kind is not None:
            self.obj.kind = self._override_kind
        return self.obj


class InterfaceComponent(Component):
    """
    A special component to be used in the `InterfaceDevice`.

    By defining a required class here, this allows us to pass
    pre-instantiated devices into the Device constructor and type-check
    them approriately.

    .. note::

        This does not set the ``parent`` attribute on the object, which will
        retain its original ``parent`` despite being adopted here.

    Parameters
    ----------
    cls : type
        Any class definition. When we pass an object into the
        `InterfaceDevice`, its type will be checked against this type.
        Any subclass of the input class type will also be accepted.

    kind : `ophydobj.Kind` or str, optional
        If provided, override the object's kind. In standard components this
        defaults to Kind.normal, but here it will default to "do not change
        the kind, leave it as is". If provided, it is up the user to make sure
        they are being consistent with the setting of kinds on their devices.
    """
    def __init__(self, cls, kind=None, **kwargs):
        self._override_kind = kind
        if kind is None:
            kind = Kind.normal
        super().__init__(cls, kind=kind, **kwargs)

    def create_component(self, instance):
        # Retrieve instance from the _interface_obj dict
        # This is assembled in InterfaceDevice.__init__
        obj = instance._interface_obj[self.attr]
        if self._override_kind is not None:
            obj.kind = self._override_kind
        return obj


class InterfaceDevice(Device):
    """
    A device that can include pre-instantiated objects on init.

    This may be useful for setting up multiple devices that need to
    re-use the same objects in different ways without needing to duplicate
    their constructor arguments.

    These pre-instantiated objects can be included by adding them as
    `InterfaceComponent` attributes in the class definition like so:

    .. code-block:: python

        from ophyd.signal import Signal
        from pcdsdevices.device import (InterfaceDevice,
                                        InterfaceComponent as ICpt)

        class MyDevice(InterfaceDevice):
            my_component = ICpt(Signal)

        my_signal = Signal(name='my_signal')
        my_device = MyDevice(
            'PREFIX', name='my_device',
            my_component=my_signal
            )

    You can automatically turn a standard `Device` into an `InterfaceDevice`
    using the `to_interface` function.
    """
    def __init__(self, *args, **kwargs):
        self._interface_obj = {}

        for cpt_name in self.component_names:
            cpt = getattr(self.__class__, cpt_name)
            if isinstance(cpt, InterfaceComponent):
                try:
                    obj = kwargs.pop(cpt_name)
                except KeyError:
                    raise TypeError(
                        f'Missing required kwarg {cpt_name}'
                        ) from None
                if isinstance(obj, cpt.cls):
                    self._interface_obj[cpt_name] = obj
                else:
                    raise TypeError(
                        f'{cpt_name} must be of type {cpt.cls}'
                        )

        super().__init__(*args, **kwargs)


def to_interface(device_class):
    """
    Convert an arbitrary `Device` into an `InterfaceDevice`.

    This will replace all components in the class definition with
    instances of `InterfaceComponent` of the original class type defined
    in the `Component`.

    Parameters
    ----------
    device_class : `Device`
        An ``ophyd`` device class that we'd like to convert.

    Returns
    -------
    interface_class : `InterfaceDevice`
        A subclass of the input ``device_class`` that has had all components
        replaced with `InterfaceComponent` instances.
    """
    interface_cpts = {}

    for cpt_name in device_class.component_names:
        cpt = getattr(device_class, cpt_name)
        interface_cpts[cpt_name] = InterfaceComponent(cpt.cls)

    return type(
        device_class.__name__ + 'Interface',
        (InterfaceDevice, device_class),
        interface_cpts
        )


class UpdateComponent(Component):
    """
    A component that copies and updates a parent component in a subclass.

    Use this like any other component, adding it to your device that is a
    subclass of another device, using the same name as the component you'd like
    to update.

    Pass keyword args to this component to update the values from the parent in
    your subclass.

    Some limitations:

    - It is not possible to use this to change the component class itself, e.g.
      if you would like to change something from a "Component" to a
      "FormattedComponent".
    - All arguments to update must be provided as keyword arguments, so we know
      which value to change in the component class.
    - UpdateComponent will always fail isinstance checks for Component
      subclasses.
    - UpdateComponent is not mutable after instantiation.

    Parameters
    ----------
    **kwargs: any, optional
        keyword arguments to update
    """
    update_kwargs: dict[str, Any]
    copt_cpt: Optional[Component]

    def __init__(self, **kwargs):
        # Note: this intentionally does not do "everything" from super
        # Store the original kwargs for use later
        self.update_kwargs = kwargs
        # Begin with "something" as the copy_cpt to avoid issues on edge cases.
        self.copy_cpt = None
        # Create a holding dict for the _subscriptions
        self._subscriptions = collections.defaultdict(list)

    def __set_name__(self, owner: Device, attr_name: str):
        # Find the parent cpt of the same name and copy it
        parent_cpt: Optional[Component] = None
        for cls in owner.mro()[1:]:
            try:
                parent_cpt = getattr(cls, attr_name)
                break
            except AttributeError:
                continue
        if parent_cpt is None:
            raise RuntimeError(
                f"Did not find component {attr_name} "
                f"on any parent class of {owner}, "
                "nothing to update!"
            )
        self.copy_cpt = copy.deepcopy(parent_cpt)

        # Edit this object as per our init args
        for key, value in self.update_kwargs.items():
            # Set the attrs if they exist
            if key == 'kind':
                # Special handling to ensure kind is a Kind
                value = (Kind[value.lower()] if isinstance(value, str)
                         else Kind(value))
                self.copy_cpt.kind = value
            elif hasattr(self.copy_cpt, key):
                setattr(self.copy_cpt, key, value)
            # Add to kwargs if they don't exist
            else:
                self.copy_cpt.kwargs[key] = value

        # Forward any of the subscriptions we've queued up prior to copy_cpt
        self.copy_cpt._subscriptions.update(self._subscriptions)
        # Replace our subs dict with the copy's so we add to the copy's
        # In case anyone does late subscription additions
        self._subscriptions = self.copy_cpt._subscriptions

        # Defer to the normal component setup for the rest
        super().__set_name__(owner, attr_name)

    def __getattr__(self, name: str):
        # If we are missing something, check the copied/edited hostage cpt
        return copy.deepcopy(getattr(self.copy_cpt, name))

    def __copy__(self):
        # Copy and return the internal component to avoid recursive loops
        return copy.copy(self.copy_cpt)

    def __deepcopy__(self, _memo):
        # Deep copy and return the internal component to avoid recursive loops
        return copy.deepcopy(self.copy_cpt)

    def create_component(self, instance):
        # Use our hostage component from __set_name__
        return self.copy_cpt.create_component(instance)


class GroupDevice(Device):
    """
    A device that is a group of components that will act independently.

    This has the following implications:
    - Components will have no references to this parent device. If
      accessed and used out of context, the components will be as if
      they were instantited completely separately.
    - The parent device will be stashed in the ``biological_parent``
      attribute, in case it's needed (by something other than the RE)
    - If a component is staged in a bluesky plan, it will not stage
      the ``GroupDevice``, and therefore will not stage the entire
      device tree.
    - ``GroupDevice`` instances by default do nothing when staged.
      You can add specific subdevices to the stage list by setting the
      ``stage_group`` class attribute to a list of components.
    - Following from the previous point, note that ``GroupDevice``
      instances cannot process top-level ``stage_sigs``. If you need
      top-level ``stage_sigs``, you should instead contain them in a
      subdevice that is not a ``GroupDevice``.
    - ``GroupDevice`` instances that implement ``set`` are required
      to specify a ``stage_group`` to help remind you that these classes
      really do need to stage "something" before scanning. If your
      movable device really does not need this, you can set ``stage_group``
      to an empty list.
    - When represented in typhos, we'll see the ``GroupDevice`` screen
      instead of the default device screens.
      (Note: at time of writing, this hypothetical ``GroupDevice``
      ui template does not yet exist).
    - Certain devices will completely break if we remove their subdevice
      references: for example, consider the ``PsuedoPositioner`` class.
      For classes like these, we'll need to keep the parent references
      for the ``PseudoSingle`` instances. For the full list of classes that
      need to retain their ``parent`` attribute, see
      ``GroupDevice.needs_parent``.
    """
    stage_group: list[Component] = None
    needs_parent: list[type[OphydObject]] = [
        AttributeSignal,
        DerivedSignal,
        PluginBase,
        PseudoSingle,
        PVStateSignal,
        AggregateSignal
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove references to parent (in this case, self)
        for cpt_name in self.component_names:
            cpt = getattr(self, cpt_name)
            # The following types break without parents
            if not isinstance(cpt, tuple(self.needs_parent)):
                cpt._parent = None
                cpt.biological_parent = self
        if self.stage_group is None:
            self.stage_group = []
        else:
            # Avoid potential issues from shared mutable class attribute
            self.stage_group = list(self.stage_group)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'set') and cls.stage_group is None:
            raise TypeError(
                f"Must specify a stage_group in {cls.__name__} because it "
                "is a movable device. See the GroupDevice docs."
                )
        if cls.stage_group is not None:
            for cpt in cls.stage_group:
                if not isinstance(cpt, Component):
                    raise TypeError(
                        f"Found non-Component {cpt} in stage_group for "
                        f"{cls.__name__}! Only Component types are allowed!"
                    )
                subcls_cpt = getattr(cls, cpt.attr, None)
                if not isinstance(subcls_cpt, Component):
                    raise TypeError(
                        f"In stage_group for {cls.__name__}, {cpt.attr} "
                        f"referenced {subcls_cpt}, which is not a Component! "
                        "Only Component types are allowed!"
                    )

    def stage_group_instances(self) -> Iterator[OphydObject]:
        """Yields an iterator of subdevices that should be staged."""
        return (getattr(self, cpt.attr) for cpt in self.stage_group)

    def stage(self) -> list[OphydObject]:
        staged = [self]
        for obj in self.stage_group_instances():
            if hasattr(obj, 'stage'):
                staged.extend(obj.stage())
        return staged

    def unstage(self) -> list[OphydObject]:
        unstaged = [self]
        for obj in reversed(list(self.stage_group_instances())):
            if hasattr(obj, 'unstage'):
                unstaged.extend(obj.unstage())
        return unstaged
