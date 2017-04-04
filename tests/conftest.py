#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
import re
import pytest
from devices.pulsepicker import PulsePickerPink


class Params:
    registry = OrderedDict()

    def __init__(self, name, cls, prefix, **kwargs):
        self.cls = cls
        self.prefix = prefix
        self.name = name
        kwargs["name"] = name
        self.kwargs = kwargs
        self.registry[name] = self

    def __del__(self):
        del self.registry[self.name]

    @classmethod
    def get(cls, param="name", regex=None):
        if regex is None:
            params = list(cls.registry.values())
        else:
            params = []
            for param_obj in cls.registry.values():
                if param == "cls":
                    string = param_obj.cls.__name__
                else:
                    try:
                        attr = getattr(param_obj, param)
                    except AttributeError:
                        attr = param_obj.kwargs[param]
                    string = str(attr)
                if re.search(string, regex):
                    params.append(param_obj)
        return params


# XCS PulsePicker
Params("pp_pink", PulsePickerPink, "XCS:SB2:MMS:09", states="XCS:SB2:PP:Y",
       ioc="XCS:IOC:PULSEPICKER:IMS", states_ioc="IOC:XCS:DEVICE:STATES")
# It should still work without the ioc arguments
Params("pp_pink_noioc", PulsePickerPink, "XCS:SB2:MMS:09",
       states="XCS:SB2:PP:Y")

all_params = Params.get()
all_labels = [p.name for p in all_params]


@pytest.fixture(scope="module",
                params=all_params,
                ids=all_labels)
def all_devices(request):
    cls = request.param.cls
    prefix = request.param.prefix
    kwargs = request.param.kwargs
    return cls(prefix, **kwargs)
