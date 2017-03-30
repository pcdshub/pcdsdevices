#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
from copy import copy
import re
import pytest
from devices.pulsepicker import PulsePickerPink


class Params:
    registry = OrderedDict()

    def __init__(self, name, cls, prefix, **kwargs):
        self.cls = cls
        self.prefix = prefix
        kwargs["name"] = name
        self.kwargs = kwargs
        self.registry[name] = self

    @classmethod
    def get(cls, param="name", regex=None):
        if regex is None:
            return copy(cls.registry)
        else:
            params = OrderedDict()
            for param_obj in cls.registry.values():
                if param == "cls":
                    string = param_obj.cls.__name__
                else:
                    string = str(getattr(param_obj, param))
                if re.search(string, regex):
                    params[param_obj.name] = param_obj
            return params


Params("pp_pink_noioc", PulsePickerPink, "XCS:SB2:MMS:09",
       in_out="XCS:SB2:PP:Y")
Params("pp_pink", PulsePickerPink, "XCS:SB2:MMS:09", in_out="XCS:SB2:PP:Y",
       ioc="XCS:IOC:PULSEPICKER:IMS", in_out_ioc="IOC:XCS:DEVICE:STATES")


@pytest.fixture(scope="module",
                params=Params.get())
def all_devices(fxt):
    cls = fxt.param.cls
    prefix = fxt.param.prefix
    kwargs = fxt.param.kwargs
    return cls(prefix, **kwargs)
