#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ophyd

VALID_OPHYD_KWARGS = ("name", "parent", "prefix", "read_attrs",
                      "configuration_attrs")


class Device(ophyd.Device):
    """
    Subclass of ophyd.Device that soaks up and stores information from the
    happi device database.
    """
    def __init__(self, prefix, **kwargs):
        db_info = kwargs.pop("db_info", None)
        if db_info:
            self.db = HappiData(db_info)
            for key in list(kwargs.keys()):
                # Remove keys in kwargs if they were from the happi import but
                # they cannot be passed to ophyd.Device
                if key in db_info and key not in VALID_OPHYD_KWARGS:
                    kwargs.pop(key)
        super().__init__(prefix, **kwargs)


class HappiData:
    """
    Class to hold data from happi in a tab-accessible format and in a
    dictionary-accessible format.
    """
    def __init__(self, db_info):
        """
        Parameters
        ----------
        db_info: dict
            Mapping from happi keyword to value
        """
        self.info = db_info
        for entry, value in db_info.items():
            setattr(self, entry, value)
