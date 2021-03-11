from ophyd.device import Device

from pcdsdevices.component import InterfaceComponent


class InterfaceDevice(Device):
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
    interface_cpts = {}

    for cpt_name in device_class.component_names:
        cpt = getattr(device_class, cpt_name)
        interface_cpts[cpt_name] = InterfaceComponent(cpt.cls)

    return type(
        device_class.__name__ + 'Interface',
        (InterfaceDevice, device_class),
        interface_cpts
        )
