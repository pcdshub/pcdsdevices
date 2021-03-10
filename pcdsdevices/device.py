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
