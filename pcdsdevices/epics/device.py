#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define functional changes to ophyd.Device. This module really only exists
because iocadmin needs to be an LCLSDevice but we must avoid the circular
dependency that arises because iocadmin should not contain another iocadmin
record.
"""
from queue import Queue
from collections import OrderedDict
from epics.ca import poll, CAThread as Thread
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
        poll()
        db_info = kwargs.get("db_info")
        if db_info:
            self.db = HappiData(db_info)
        kwargs = {k: v for k, v in kwargs.items() if k in VALID_OPHYD_KWARGS}
        super().__init__(prefix, **kwargs)

    def get(self, **kwargs):
        values = self._list_values(self.signal_names, method="get",
                                   config=False, attr_keys=True, **kwargs)
        return self._device_tuple(**values)

    def _read_attr_list(self, attr_list, *, config=False):
        return self._list_values(attr_list, method="read", config=config,
                                 attr_keys=False)

    def _describe_attr_list(self, attr_list, *, config=False):
        return self._list_values(attr_list, method="describe", config=config,
                                 attr_keys=False)

    def _list_values(self, attr_list, *, method="get", config=False,
                     attr_keys=True, **kwargs):
        """
        For attr in attr_list, call attr.method(**kwargs) in separate threads,
        assembling the results in an OrderedDict with the same order as
        attr_list.
        """
        values = OrderedDict()
        value_queue = Queue()
        threads = []
        if config:
            method += "_configuration"
        for attr in attr_list:
            if attr_keys:
                values[attr] = None
            thread = Thread(target=self._value_thread,
                            args=(attr, method, value_queue),
                            kwargs=kwargs)
            threads.append(thread)
            thread.start()
        for t in threads:
            t.join()
        while not value_queue.empty():
            attr, value = value_queue.get()
            if isinstance(value, dict) and not attr_keys:
                values.update(value)
            else:
                values[attr] = value
        return values

    def _value_thread(self, attr, method, value_queue, **kwargs):
        """
        Call attr.method(**kwargs) and put to the value queue.
        """
        try:
            obj = getattr(self, attr)
            func = getattr(obj, method)
            value = func(**kwargs)
        except:
            value = None
        value_queue.put((attr, value))


class HappiData:
    def __init__(self, db_info):
        self.info = db_info
        for entry, value in db_info.items():
            setattr(self, entry, value)
