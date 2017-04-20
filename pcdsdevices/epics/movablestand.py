#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .state import pvstate_class

MovableStand = pvstate_class("MovableStand",
                             {"in_limit": {"pvname": ":IN_DI",
                                           0: "defer",
                                           1: "IN"},
                              "out_limit": {"pvname": ":OUT_DO",
                                            0: "defer",
                                            1: "OUT"}})
