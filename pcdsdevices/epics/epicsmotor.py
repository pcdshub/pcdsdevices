#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ophyd
from .device import Device

class EpicsMotor(ophyd.EpicsMotor, Device):
    pass
