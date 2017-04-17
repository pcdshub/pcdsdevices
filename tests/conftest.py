#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict
import re
import pytest
from pcdsdevices import (ImsMotor, GateValve, Slits, Attenuator,
                         PulsePickerPink, Stopper, PPSStopper)


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


# XCS Last User Motor
Params("xcs_ims_usr32", ImsMotor, "XCS:USR:MMS:32", ioc="IOC:XCS:USR:DUMB:IMS")
# XCS Random Gate Valve
Params("xcs_lam_valve1", GateValve, "XCS:LAM:VGC:01", ioc="XCS:R51:IOC:39")
# XCS slits
Params("xcs_slits6", Slits, "XCS:SB2:DS:JAWS", ioc="IOC:XCS:SB2:SLITS:IMS")
# XCS PulsePicker
Params("pp_pink", PulsePickerPink, "XCS:SB2:MMS:09", states="XCS:SB2:PP:Y",
       ioc="XCS:IOC:PULSEPICKER:IMS", states_ioc="IOC:XCS:DEVICE:STATES")
# XCS Attenuator
Params("xcs_att", Attenuator, "XCS:ATT", n_filters=10, ioc="IOC:XCS:ATT")
# CXI DG3 Stopper
Params("h5_stopper", Stopper, "HFX:DG3:STOP:01")
# CXI PPS Stopper
Params("s5_pps_stopper", PPSStopper, "PPS:FEH1:5:S5:STPRSUM")


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
