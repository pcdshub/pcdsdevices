from ophyd.device import Component, Device


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

    Parameters
    ----------
    obj : object
        Any existing object. This will be included in the Device as a proper
        component, as if it was constructed by the class itself.
    """
    def __init__(self, obj):
        super().__init__(object)
        self.obj = obj

    def create_component(self, instance):
        return self.obj


class InterfaceComponent(Component):
    """
    A special component to be used in the `InterfaceDevice`.

    By defining a required class here, this allows us to pass
    pre-instantiated devices into the Device constructor and type-check
    them approriately.

    Parameters
    ----------
    cls : type
        Any class definition. When we pass an object into the
        `InterfaceDevice`, its type will be checked against this type.
        Any subclass of the input class type will also be accepted.
    """
    def create_component(self, instance):
        return instance._interface_obj[self.attr]


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
