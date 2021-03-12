from ophyd.device import Device

from pcdsdevices.component import InterfaceComponent


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
        from pcdsdevices.device import InterfaceDevice
        from pcdsdevices.component import InterfaceComponent as ICpt

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
