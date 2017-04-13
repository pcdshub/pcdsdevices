#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Overrides to ophyd.Device that are relevant for epics devices.
"""
from queue import Queue
from collections import OrderedDict

from epics.ca import poll, CAThread as Thread
# from ophyd.utils import doc_annotation_forwarder

from ..device import Device


class Device(Device):
    """
    Provides the following tweaks to ophyd.Device:
    * call "poll()" after __init__ to magically fix .get() bug
    * get, read, and describe gather values in parallel threads so we don't
      time out in series
    """
    def __init__(self, prefix, **kwargs):
        poll()
        super().__init__(prefix, **kwargs)

    # @doc_annotation_forwarder(Device)
    def get(self, **kwargs):
        values = self._list_values(self.signal_names, method="get",
                                   config=False, attr_keys=True, **kwargs)
        return self._device_tuple(**values)

    # @doc_annotation_forwarder(Device)
    def _read_attr_list(self, attr_list, *, config=False):
        return self._list_values(attr_list, method="read", config=config,
                                 attr_keys=False)

    # @doc_annotation_forwarder(Device)
    def _describe_attr_list(self, attr_list, *, config=False):
        return self._list_values(attr_list, method="describe", config=config,
                                 attr_keys=False)

    def _list_values(self, attr_list, *, method="get", config=False,
                     attr_keys=True, **kwargs):
        """
        For attr in attr_list, call attr.method(**kwargs) in separate threads,
        assembling the results in an OrderedDict with the same order as
        attr_list.

        Parameters
        ----------
        attr_list: list of str
            Names of attributes to use
        method: str, optional
            Method to call on each attribute to get the value. If omitted,
            defaults to "get".
        config: bool, optional
            If True, calls method + "_configuration" instead of method.
            Defaults to False.
        attr_keys: bool, optional
            If False, update dictionaries into the main dictionary. Defaults to
            True.
        **kwargs: extra arguments to pass to the method.

        Returns
        -------
        values: OrderedDict
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

        Parameters
        ----------
        attr: str
            Name of attribute to use.
        method: str
            Method to call of the attribute.
        value_queue: Queue
            Threadsafe queue to store the output
        **kwargs: pass additional arguments to the method
        """
        try:
            obj = getattr(self, attr)
            func = getattr(obj, method)
            value = func(**kwargs)
        except:
            value = None
        value_queue.put((attr, value))
