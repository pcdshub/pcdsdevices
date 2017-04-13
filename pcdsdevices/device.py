#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define functional changes to ophyd.Device. This module really only exists
because iocadmin needs to be an LCLSDevice but we must avoid the circular
dependency that arises because iocadmin should not contain another iocadmin
record.
"""
import ophyd

# ophyd.Device claims to accept extra **kwargs, but does not use them. One of
# its parent classes, OphydObject, does not have **kwargs in the __init__
# statement and will throw an exception. We use this list to lay a safety net
# and avoid raising an exception in OphydObject.__init__
VALID_OPHYD_KWARGS = ("name", "parent", "prefix", "read_attrs",
                      "configuration_attrs")


class Device(ophyd.Device):
    """
    Tweaks to Ophyd.Device
    """
    def __init__(self, prefix, **kwargs):
        # Bizarrely, this poll call in conjunction with lazy=True fixes an
        # issue where calling .get early could fail.
        db_info = kwargs.get("db_info")
        if db_info:
            self.db = HappiData(db_info)
        kwargs = {k: v for k, v in kwargs.items() if k in VALID_OPHYD_KWARGS}
        super().__init__(prefix, **kwargs)


class HappiData:
    def __init__(self, db_info):
        self.info = db_info
        for entry, value in db_info.items():
            setattr(self, entry, value)
