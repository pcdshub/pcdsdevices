from ophyd.device import Component


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

        from pcdsdevices.component import UnrelatedComponent as UCpt

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
